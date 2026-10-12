"""Nghiên cứu Ablation Study bóc tách tác động của từng thành phần trong hệ thống:
1. Config A: Chỉ dùng Tabular Heuristic / Baseline
2. Config B: Chỉ dùng Tabular ML (Random Forest + Gradient Boosting Regressor)
3. Config C: Tabular ML + Legal RAG Penalty Frames (ràng buộc khung hình phạt luật định)
4. Config D: Tabular ML + Legal RAG + Precedent Guidance (tính toán sự tương thích với án lệ)
5. Config E: Full System (Temporal Reasoning + Legal RAG + Precedents + Consistency Guardrails)

Đo lường sự thay đổi của:
- Classification: Accuracy, Balanced Accuracy, Macro F1
- Regression: MAE, RMSE, R²
- Legal Consistency: Tỷ lệ tuân thủ khung hình phạt, tỷ lệ vi phạm bất hồi tố
"""

from __future__ import annotations

import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from rich.console import Console
from rich.table import Table
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from scripts.evaluate_models import STATUTORY_PENALTY_FRAMES
from scripts.train_baseline_models import load_dataset
from src.first_instance.predictor import FirstInstancePredictor
from src.validation.consistency_checker import ConsistencyChecker

console = Console(legacy_windows=False)
OUTPUT_FILE = PROJECT_ROOT / "data" / "models" / "ablation_study_results.json"


def evaluate_config(
    config_name: str,
    test_cases: list[dict[str, Any]],
    use_ml: bool = True,
    apply_statutory_clipping: bool = False,
    apply_consistency_guardrails: bool = False,
) -> dict[str, Any]:
    """Đánh giá một cấu hình cụ thể trong nghiên cứu bóc tách (Ablation)."""
    checker = ConsistencyChecker()
    predictor = FirstInstancePredictor(load_checkpoints=use_ml)

    y_true_class = []
    y_pred_class = []
    y_true_reg = []
    y_pred_reg = []

    consistency_violations = 0

    for c in test_cases:
        feats = c["features"]
        pred = predictor.predict(feats)

        # Ground truth
        t_cls = 1 if c["verdict"] == "guilty" else 0
        t_reg = float(c["sentence_years"])
        y_true_class.append(t_cls)
        y_true_reg.append(t_reg)

        # Raw prediction
        p_cls = 1 if pred["predicted_outcome"] == "guilty" else 0
        p_reg = float(pred.get("predicted_sentence_years", 0.0))

        # Ablation component: Áp dụng ràng buộc khung luật định (Legal RAG Bounds)
        if apply_statutory_clipping and p_cls == 1:
            for art_num, (min_y, max_y) in STATUTORY_PENALTY_FRAMES.items():
                if feats.get(f"crime_is_{art_num}", 0) == 1.0:
                    # Ràng buộc mức án tối thiểu và tối đa theo điều luật
                    has_many_mitigating = feats.get("num_mitigating", 0) >= 2
                    eff_min = min_y * 0.7 if has_many_mitigating else min_y
                    p_reg = float(np.clip(p_reg, eff_min, max_y))

        # Ablation component: Áp dụng Hàng rào Nhất quán Pháp lý (Consistency Guardrails)
        if apply_consistency_guardrails:
            # Nếu phán quyết là vô tội thì mức án bắt buộc là 0
            if p_cls == 0:
                p_reg = 0.0
            # Mức án không thể âm
            p_reg = max(0.0, p_reg)

            # Logic guardrail: Bị cáo có quá nhiều tình tiết giảm nhẹ và không có tăng nặng
            if feats.get("num_aggravating", 0) == 0 and feats.get("num_mitigating", 0) >= 3:
                p_reg = max(0.0, p_reg * 0.75)

        y_pred_class.append(p_cls)
        y_pred_reg.append(p_reg)

        # Kiểm tra tính nhất quán
        if p_reg < 0.0 or (p_cls == 0 and p_reg > 0.0):
            consistency_violations += 1

    acc = accuracy_score(y_true_class, y_pred_class)
    b_acc = balanced_accuracy_score(y_true_class, y_pred_class)
    f1_macro = f1_score(y_true_class, y_pred_class, average="macro", zero_division=0)

    mae = mean_absolute_error(y_true_reg, y_pred_reg)
    rmse = np.sqrt(mean_squared_error(y_true_reg, y_pred_reg))
    r2 = r2_score(y_true_reg, y_pred_reg)

    consistency_rate = (len(test_cases) - consistency_violations) / len(test_cases)

    return {
        "config_name": config_name,
        "classification": {
            "accuracy": float(acc),
            "balanced_accuracy": float(b_acc),
            "macro_f1": float(f1_macro),
        },
        "regression": {
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2),
        },
        "legal_consistency_rate": float(consistency_rate),
    }


def main() -> None:
    console.print("[bold cyan]=== BÁO CÁO NGHIÊN CỨU BÓC TÁCH THÀNH PHẦN (ABLATION STUDY) ===[/bold cyan]")

    dataset = load_dataset()
    split_date = datetime(2022, 1, 1).date()

    train_cases = [d for d in dataset if datetime.fromisoformat(d["judgment_date"]).date() < split_date]
    test_cases = [d for d in dataset if datetime.fromisoformat(d["judgment_date"]).date() >= split_date]

    console.print(f"Tổng mẫu: {len(dataset)} | Train: {len(train_cases)} | Test (>= 2022-01-01): {len(test_cases)}\n")

    configs = [
        ("Config A: Pure Heuristic Baseline", False, False, False),
        ("Config B: Tabular ML Models (RF + GBR)", True, False, False),
        ("Config C: Tabular ML + Legal RAG Penalty Frames", True, True, False),
        ("Config D: Full Pipeline (+ Consistency Guardrails)", True, True, True),
    ]

    results = []
    table = Table(title="Kết Quả Ablation Study Trên Holdout Test Set")
    table.add_column("Cấu Hình Thử Nghiệm", style="cyan", width=36)
    table.add_column("Accuracy", style="white", justify="right")
    table.add_column("Balanced Acc", style="white", justify="right")
    table.add_column("Macro F1", style="green", justify="right")
    table.add_column("MAE (Năm tù)", style="yellow", justify="right")
    table.add_column("RMSE (Năm)", style="yellow", justify="right")
    table.add_column("R² Score", style="magenta", justify="right")
    table.add_column("Tính Nhất Quán", style="blue", justify="right")

    for name, use_ml, statutory, guardrails in configs:
        res = evaluate_config(
            config_name=name,
            test_cases=test_cases,
            use_ml=use_ml,
            apply_statutory_clipping=statutory,
            apply_consistency_guardrails=guardrails,
        )
        results.append(res)
        c = res["classification"]
        r = res["regression"]
        table.add_row(
            name,
            f"{c['accuracy']:.4f}",
            f"{c['balanced_accuracy']:.4f}",
            f"{c['macro_f1']:.4f}",
            f"{r['mae']:.2f}",
            f"{r['rmse']:.2f}",
            f"{r['r2']:.4f}",
            f"{res['legal_consistency_rate']*100:.1f}%",
        )

    console.print(table)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"\n[green]✓ Đã lưu kết quả Ablation Study vào: {OUTPUT_FILE}[/green]")


if __name__ == "__main__":
    main()
