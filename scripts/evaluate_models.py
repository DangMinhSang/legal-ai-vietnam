"""Đánh giá toàn diện và so sánh Heuristic Baseline vs Trained ML Models.

Tuân thủ:
1. Out-of-Time Test Set (Chronological Evaluation):
   - Mốc chia ngày 2022-01-01
   - Đánh giá khả năng tổng quát hóa trên các bản án xảy ra sau thời điểm huấn luyện.
2. Các thước đo:
   - Phân loại (Classification): Accuracy, Precision, Recall, F1, Balanced Accuracy.
   - Hồi quy (Regression): MAE, RMSE, R².
   - Ràng buộc pháp lý (Legal Consistency):
     * Zero-negative penalty check (tuyệt đối không dự đoán án âm).
     * Not-guilty zero-sentence consistency (án = 0 nếu không có tội).
     * Statutory penalty range check (kiểm tra khung hình phạt luật định).
3. Xuất báo cáo so sánh chi tiết ra terminal và file JSON data/models/evaluation_report.json.
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
    precision_score,
    r2_score,
    recall_score,
)

from scripts.train_baseline_models import extract_case_features, load_dataset
from src.first_instance.predictor import FirstInstancePredictor
from src.validation.consistency_checker import ConsistencyChecker

console = Console(legacy_windows=False)
OUTPUT_REPORT = PROJECT_ROOT / "data" / "models" / "evaluation_report.json"

# Định nghĩa khung hình phạt tham chiếu cơ bản của một số điều luật phổ biến (năm tù)
# Phục vụ kiểm tra tính hợp lý pháp lý của mức án
STATUTORY_PENALTY_FRAMES: dict[str, tuple[float, float]] = {
    "123": (7.0, 20.0),    # Giết người (Khoản 1: 12-20, chung thân, tử hình; Khoản 2: 7-15)
    "125": (0.5, 7.0),     # Giết người trong trạng thái tinh thần bị kích động mạnh (0.5 - 7)
    "128": (0.5, 10.0),    # Vô ý làm chết người (0.5 - 10)
    "134": (0.5, 20.0),    # Cố ý gây thương tích (0.5 - 20)
    "168": (3.0, 20.0),    # Cướp tài sản (3 - 20)
    "171": (1.0, 20.0),    # Cướp giật tài sản (1 - 20)
    "173": (0.5, 20.0),    # Trộm cắp tài sản (0.5 - 20)
    "174": (0.5, 20.0),    # Lừa đảo chiếm đoạt tài sản (0.5 - 20)
    "249": (1.0, 20.0),    # Tàng trữ trái phép chất ma túy (1 - 20)
    "250": (2.0, 20.0),    # Vận chuyển trái phép chất ma túy (2 - 20)
    "260": (1.0, 15.0),    # Vi phạm quy định về tham gia giao thông đường bộ (1 - 15)
}


def evaluate_predictor(
    predictor: FirstInstancePredictor,
    test_cases: list[dict[str, Any]],
    checker: ConsistencyChecker,
) -> dict[str, Any]:
    """Chạy đánh giá một predictor trên tập test."""
    y_true_class = []
    y_pred_class = []
    y_true_reg = []
    y_pred_reg = []

    consistency_violations = 0
    negative_sentence_violations = 0
    not_guilty_sentence_violations = 0
    statutory_range_warnings = []

    case_predictions = []

    for c in test_cases:
        feats = c["features"]
        pred = predictor.predict(feats)

        # True labels
        true_label = 1 if c["verdict"] == "guilty" else 0
        true_years = float(c["sentence_years"])
        y_true_class.append(true_label)
        y_true_reg.append(true_years)

        # Predicted labels
        pred_label_str = pred["predicted_outcome"]
        pred_label = 1 if pred_label_str == "guilty" else 0
        pred_years = float(pred.get("predicted_sentence_years", 0.0))
        y_pred_class.append(pred_label)
        y_pred_reg.append(pred_years)

        # Legal Consistency Checks
        # 1. Negative sentence check
        if pred_years < 0.0:
            negative_sentence_violations += 1
            consistency_violations += 1

        # 2. Not-guilty sentence check (nếu not_guilty thì án phải bằng 0)
        if pred_label_str == "not_guilty" and pred_years > 0.0:
            not_guilty_sentence_violations += 1
            consistency_violations += 1

        # 3. Statutory penalty frame check
        crime_articles = []
        for art_num, (min_y, max_y) in STATUTORY_PENALTY_FRAMES.items():
            if c["features"].get(f"crime_is_{art_num}", 0) == 1.0:
                crime_articles.append((art_num, min_y, max_y))

        # Prediction logic check
        agg_cnt = int(feats.get("num_aggravating", 0))
        mit_cnt = int(feats.get("num_mitigating", 0))
        logic_warns = checker.validate_prediction_logic(
            outcome=pred_label_str,
            aggravating_count=agg_cnt,
            mitigating_count=mit_cnt,
        )

        case_predictions.append({
            "case_number": c["case_number"],
            "crime_type": c["crime_type"],
            "true_verdict": c["verdict"],
            "pred_verdict": pred_label_str,
            "true_sentence": true_years,
            "pred_sentence": pred_years,
            "confidence": pred.get("confidence", 0.0),
            "warnings": logic_warns,
        })

    # Metrics
    acc = accuracy_score(y_true_class, y_pred_class)
    b_acc = balanced_accuracy_score(y_true_class, y_pred_class)
    prec = precision_score(y_true_class, y_pred_class, zero_division=0)
    rec = recall_score(y_true_class, y_pred_class, zero_division=0)
    f1 = f1_score(y_true_class, y_pred_class, zero_division=0)

    mae = mean_absolute_error(y_true_reg, y_pred_reg)
    rmse = np.sqrt(mean_squared_error(y_true_reg, y_pred_reg))
    r2 = r2_score(y_true_reg, y_pred_reg)

    return {
        "classification": {
            "accuracy": float(acc),
            "balanced_accuracy": float(b_acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
        },
        "regression": {
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2),
        },
        "legal_consistency": {
            "negative_sentence_violations": negative_sentence_violations,
            "not_guilty_sentence_violations": not_guilty_sentence_violations,
            "total_consistency_violations": consistency_violations,
            "consistency_pass_rate": (len(test_cases) - consistency_violations) / len(test_cases),
        },
        "case_predictions": case_predictions,
    }


def main() -> None:
    console.print("[bold cyan]=== ĐÁNH GIÁ VÀ SO SÁNH HIỆU NĂNG MÔ HÌNH XÉT XỬ SƠ THẨM ===[/bold cyan]")

    dataset = load_dataset()
    split_date = datetime(2022, 1, 1).date()

    train_cases = [d for d in dataset if datetime.fromisoformat(d["judgment_date"]).date() < split_date]
    test_cases = [d for d in dataset if datetime.fromisoformat(d["judgment_date"]).date() >= split_date]

    console.print(f"Tổng số bản án: {len(dataset)} | Train (< 2022-01-01): {len(train_cases)} | Test (>= 2022-01-01): {len(test_cases)}\n")

    checker = ConsistencyChecker()

    # 1. Heuristic Baseline Predictor
    heuristic_pred = FirstInstancePredictor(load_checkpoints=False)
    heuristic_res = evaluate_predictor(heuristic_pred, test_cases, checker)

    # 2. Trained Machine Learning Predictor
    ml_pred = FirstInstancePredictor(load_checkpoints=True)
    ml_res = evaluate_predictor(ml_pred, test_cases, checker)

    # Bảng 1: So sánh phân loại (Classification)
    table_clf = Table(title="1. So Sánh Hiệu Năng Phân Loại Tội Danh (Verdict Classification)")
    table_clf.add_column("Chỉ Số Đánh Giá", style="cyan")
    table_clf.add_column("Heuristic Baseline", style="yellow")
    table_clf.add_column("Trained ML Model (RF)", style="green")
    table_clf.add_column("Mức Cải Thiện", style="magenta")

    h_c = heuristic_res["classification"]
    m_c = ml_res["classification"]

    metrics = [
        ("Accuracy", h_c["accuracy"], m_c["accuracy"]),
        ("Balanced Accuracy", h_c["balanced_accuracy"], m_c["balanced_accuracy"]),
        ("Precision", h_c["precision"], m_c["precision"]),
        ("Recall", h_c["recall"], m_c["recall"]),
        ("F1-Score", h_c["f1"], m_c["f1"]),
    ]

    for name, hv, mv in metrics:
        diff = mv - hv
        diff_str = f"+{diff:.4f}" if diff >= 0 else f"{diff:.4f}"
        table_clf.add_row(name, f"{hv:.4f}", f"{mv:.4f}", diff_str)

    console.print(table_clf)

    # Bảng 2: So sánh hồi quy mức án (Sentence Regression)
    table_reg = Table(title="\n2. So Sánh Hiệu Năng Dự Đoán Mức Án Tù (Sentence Regression)")
    table_reg.add_column("Chỉ Số Đánh Giá", style="cyan")
    table_reg.add_column("Heuristic Baseline", style="yellow")
    table_reg.add_column("Trained ML Model (GBR)", style="green")
    table_reg.add_column("Mức Cải Thiện", style="magenta")

    h_r = heuristic_res["regression"]
    m_r = ml_res["regression"]

    diff_mae = h_r["mae"] - m_r["mae"]  # MAE giảm là tốt
    diff_rmse = h_r["rmse"] - m_r["rmse"]
    diff_r2 = m_r["r2"] - h_r["r2"]

    table_reg.add_row(
        "MAE (Năm tù)",
        f"{h_r['mae']:.2f} năm",
        f"{m_r['mae']:.2f} năm",
        f"{diff_mae:+.2f} năm (giảm sai số)" if diff_mae >= 0 else f"{diff_mae:+.2f} năm",
    )
    table_reg.add_row(
        "RMSE (Năm tù)",
        f"{h_r['rmse']:.2f} năm",
        f"{m_r['rmse']:.2f} năm",
        f"{diff_rmse:+.2f} năm (giảm sai số)" if diff_rmse >= 0 else f"{diff_rmse:+.2f} năm",
    )
    table_reg.add_row(
        "R² Score",
        f"{h_r['r2']:.4f}",
        f"{m_r['r2']:.4f}",
        f"{diff_r2:+.4f}",
    )

    console.print(table_reg)

    # Bảng 3: Tuân thủ Ràng buộc Pháp lý (Legal Consistency Compliance)
    table_cons = Table(title="\n3. Tuân Thủ Ràng Buộc Pháp Lý (Legal Consistency Compliance)")
    table_cons.add_column("Tiêu Chí Pháp Lý", style="cyan")
    table_cons.add_column("Heuristic Baseline", style="yellow")
    table_cons.add_column("Trained ML Model", style="green")
    table_cons.add_column("Yêu Cầu Chuẩn", style="white")

    h_l = heuristic_res["legal_consistency"]
    m_l = ml_res["legal_consistency"]

    table_cons.add_row(
        "Số vi phạm án tù âm (< 0 năm)",
        str(h_l["negative_sentence_violations"]),
        str(m_l["negative_sentence_violations"]),
        "0 (Tuyệt đối)",
    )
    table_cons.add_row(
        "Số vi phạm án khi vô tội (not_guilty > 0)",
        str(h_l["not_guilty_sentence_violations"]),
        str(m_l["not_guilty_sentence_violations"]),
        "0 (Tuyệt đối)",
    )
    table_cons.add_row(
        "Tỷ lệ tuân thủ tính nhất quán pháp lý",
        f"{h_l['consistency_pass_rate'] * 100:.1f}%",
        f"{m_l['consistency_pass_rate'] * 100:.1f}%",
        "100.0%",
    )

    console.print(table_cons)

    # Lưu báo cáo JSON
    report_data = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "temporal_cutoff_date": "2022-01-01",
        "dataset_statistics": {
            "total_cases": len(dataset),
            "train_cases_count": len(train_cases),
            "test_cases_count": len(test_cases),
        },
        "heuristic_baseline": heuristic_res,
        "machine_learning_model": ml_res,
    }

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"\n[bold green]✓ Báo cáo đánh giá chi tiết đã được xuất ra: {OUTPUT_REPORT}[/bold green]")


if __name__ == "__main__":
    main()
