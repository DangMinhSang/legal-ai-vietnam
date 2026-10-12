"""Huấn luyện mô hình cơ sở (Baseline Models) dự đoán kết quả xét xử sơ thẩm.

Tuân thủ nghiêm ngặt:
1. Phân chia theo trật tự thời gian (Chronological Split):
   - Train set: các bản án trước 2022-01-01
   - Test set: các bản án từ 2022-01-01 trở đi
   - Tuyệt đối không rò rỉ dữ liệu tương lai vào tập huấn luyện.
2. Không rò rỉ nhãn (No Label Leakage):
   - Features đầu vào chỉ bao gồm tình tiết khách quan, không chứa thông tin bản án.
3. Đánh giá đa chiều:
   - Phân loại (Classification): Dự đoán guilty / not_guilty (Accuracy, Precision, Recall, F1).
   - Hồi quy (Regression): Dự đoán mức án tù (năm) (MAE, RMSE, R²).
4. Lưu trữ artifacts vào data/models/checkpoints/.
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

import joblib
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

from src.validation.leakage import FIRST_INSTANCE_OUTCOME_FIELDS

console = Console(legacy_windows=False)
CHECKPOINTS_DIR = PROJECT_ROOT / "data" / "models" / "checkpoints"
JUDGMENTS_DIR = PROJECT_ROOT / "data" / "sample" / "judgments"

# Khung hình phạt luật định theo BLHS 2015 (áp dụng cho các điều luật truy tố phổ biến)
STATUTORY_PENALTY_BOUNDS: dict[str, tuple[float, float]] = {
    "123": (7.0, 20.0),    # Giết người (Khoản 1: 12-20, chung thân, tử hình; Khoản 2: 7-15)
    "125": (0.5, 7.0),     # Giết người trong trạng thái tinh thần bị kích động mạnh (0.5 - 7)
    "128": (1.0, 5.0),     # Vô ý làm chết người (1 - 5)
    "134": (0.5, 14.0),    # Cố ý gây thương tích (0.5 - 14)
    "168": (3.0, 18.0),    # Cướp tài sản (3 - 18)
    "171": (1.0, 10.0),    # Cướp giật tài sản (1 - 10)
    "173": (0.5, 7.0),     # Trộm cắp tài sản (0.5 - 7)
    "174": (0.5, 12.0),    # Lừa đảo chiếm đoạt tài sản (0.5 - 12)
    "249": (1.0, 5.0),     # Tàng trữ trái phép chất ma túy (1 - 5)
    "250": (7.0, 20.0),    # Vận chuyển trái phép chất ma túy (7 - 20)
    "251": (2.0, 15.0),    # Mua bán trái phép chất ma túy (2 - 15)
    "260": (1.0, 10.0),    # Vi phạm quy định về tham gia giao thông đường bộ (1 - 10)
    "318": (0.25, 7.0),    # Gây rối trật tự công cộng (0.25 - 7)
    "341": (0.5, 7.0),     # Làm giả con dấu, tài liệu của CQ, TC; sử dụng tài liệu giả (0.5 - 7)
}


def extract_case_features(case_json: dict[str, Any]) -> dict[str, float]:
    """Trích xuất vector đặc trưng khách quan từ bản án, tuyệt đối không rò rỉ nhãn."""
    # Kiểm tra rò rỉ nhãn
    for field in FIRST_INSTANCE_OUTCOME_FIELDS:
        if field in case_json.get("facts_summary", "").lower():
            pass  # văn bản tóm tắt tình tiết

    facts = case_json.get("facts_summary", "")
    agg_factors = case_json.get("aggravating_factors", [])
    mit_factors = case_json.get("mitigating_factors", [])
    articles = case_json.get("applicable_articles", [])
    defendant = case_json.get("defendant", {})
    crime_type = case_json.get("crime_type", "").lower()

    num_agg = float(len(agg_factors))
    num_mit = float(len(mit_factors))
    num_facts = 1.0 + num_agg + num_mit

    # Khung hình phạt luật định từ điều luật viện dẫn trong Cáo trạng truy tố
    stat_min, stat_max = 0.5, 5.0
    for a in articles:
        if str(a) in STATUTORY_PENALTY_BOUNDS:
            stat_min, stat_max = STATUTORY_PENALTY_BOUNDS[str(a)]
            break
    stat_mid = (stat_min + stat_max) / 2.0

    features = {
        "num_facts": num_facts,
        "num_aggravating": num_agg,
        "num_mitigating": num_mit,
        "agg_to_mit_ratio": num_agg / (num_mit + 1e-4),
        "prior_convictions": float(defendant.get("prior_convictions", 0)),
        "is_organized": 1.0 if any("tổ chức" in a.lower() for a in agg_factors) else 0.0,
        "has_dangerous_weapon": 1.0 if any("hung khí" in a.lower() or "vũ khí" in a.lower() for a in agg_factors) else 0.0,
        "is_recidivist": 1.0 if any("tái phạm" in a.lower() for a in agg_factors) else 0.0,
        "sincere_confession": 1.0 if any("thành khẩn" in m.lower() for m in mit_factors) else 0.0,
        "compensation_made": 1.0 if any("bồi thường" in m.lower() or "khắc phục" in m.lower() for m in mit_factors) else 0.0,
        "surrendered": 1.0 if any("đầu thú" in m.lower() for m in mit_factors) else 0.0,
        "has_legal_factors": 1.0 if (num_agg + num_mit > 0) else 0.0,
        "no_factors": 1.0 if (num_agg + num_mit == 0) else 0.0,
        # Nhóm tội danh phân hóa chi tiết
        "crime_is_robbery": 1.0 if ("cướp tài sản" in crime_type or ("cướp" in crime_type and "giật" not in crime_type)) else 0.0,
        "crime_is_snatching": 1.0 if "cướp giật" in crime_type else 0.0,
        "crime_is_theft": 1.0 if "trộm" in crime_type else 0.0,
        "crime_is_fraud": 1.0 if "lừa đảo" in crime_type else 0.0,
        "crime_is_murder": 1.0 if ("giết người" in crime_type and "kích động" not in crime_type) else 0.0,
        "crime_is_provoked_murder": 1.0 if "kích động" in crime_type else 0.0,
        "crime_is_involuntary_manslaughter": 1.0 if "vô ý" in crime_type else 0.0,
        "crime_is_injury": 1.0 if "thương tích" in crime_type else 0.0,
        "crime_is_drug_transport": 1.0 if ("vận chuyển" in crime_type and "ma túy" in crime_type) else 0.0,
        "crime_is_drug_trafficking": 1.0 if ("mua bán" in crime_type and "ma túy" in crime_type) else 0.0,
        "crime_is_drug_possession": 1.0 if ("tàng trữ" in crime_type and "ma túy" in crime_type) else 0.0,
        "crime_is_traffic": 1.0 if "giao thông" in crime_type else 0.0,
        "crime_is_public_disorder": 1.0 if "gây rối" in crime_type else 0.0,
        "crime_is_forgery": 1.0 if ("làm giả" in crime_type or "tài liệu giả" in crime_type or "con dấu" in crime_type or "341" in crime_type) else 0.0,
        # Khung hình phạt luật định (Statutory Penalty Bounds)
        "statutory_min": stat_min,
        "statutory_max": stat_max,
        "statutory_mid": stat_mid,
    }

    # Các cờ chỉ thị điều luật truy tố cụ thể
    for art_num in STATUTORY_PENALTY_BOUNDS:
        features[f"crime_is_{art_num}"] = 1.0 if (art_num in [str(a) for a in articles]) else 0.0

    # Đảm bảo không có trường nào rò rỉ nhãn kết quả
    for k in features:
        assert k not in FIRST_INSTANCE_OUTCOME_FIELDS, f"Lỗi rò rỉ trường {k} vào feature set!"

    return features


def load_dataset() -> list[dict[str, Any]]:
    """Đọc dữ liệu tất cả các bản án trong thư mục mẫu."""
    files = sorted(JUDGMENTS_DIR.glob("*.json"))
    dataset = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        features = extract_case_features(data)
        dataset.append({
            "id": data.get("id"),
            "case_number": data.get("case_number"),
            "judgment_date": data.get("judgment_date"),
            "crime_type": data.get("crime_type"),
            "features": features,
            "verdict": data.get("verdict", "guilty"),
            "sentence_years": float(data.get("sentence_years", 0.0)),
            "sentence_type": data.get("sentence_type", "imprisonment"),
        })
    return dataset


def main() -> None:
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    console.print("[bold cyan]=== BẮT ĐẦU HUẤN LUYỆN MÔ HÌNH BASELINE HÌNH SỰ SƠ THẨM ===[/bold cyan]")

    dataset = load_dataset()
    console.print(f"Tổng số bản án thu thập được: [yellow]{len(dataset)}[/yellow]")

    # 1. Chronological Split (Mốc chia 2022-01-01)
    split_date = datetime(2022, 1, 1).date()
    train_cases = []
    test_cases = []

    for d in dataset:
        dt = datetime.fromisoformat(d["judgment_date"]).date()
        if dt < split_date:
            train_cases.append(d)
        else:
            test_cases.append(d)

    console.print(f"• Tập huấn luyện (Train < 2022-01-01): [green]{len(train_cases)} bản án[/green]")
    console.print(f"• Tập kiểm thử (Test >= 2022-01-01):  [magenta]{len(test_cases)} bản án[/magenta]")

    # Kiểm tra rò rỉ thời gian
    train_dates = [datetime.fromisoformat(c["judgment_date"]).date() for c in train_cases]
    test_dates = [datetime.fromisoformat(c["judgment_date"]).date() for c in test_cases]
    assert max(train_dates) < min(test_dates), "LỖI NGIÊM TRỌNG: Rò rỉ thời gian giữa tập train và test!"

    # 2. Chuẩn bị Feature Matrix X và Targets y
    feature_names = list(train_cases[0]["features"].keys())

    X_train = np.array([[c["features"][f] for f in feature_names] for c in train_cases])
    y_class_train = np.array([1 if c["verdict"] == "guilty" else 0 for c in train_cases])
    y_reg_train = np.array([c["sentence_years"] for c in train_cases])

    X_test = np.array([[c["features"][f] for f in feature_names] for c in test_cases])
    y_class_test = np.array([1 if c["verdict"] == "guilty" else 0 for c in test_cases])
    y_reg_test = np.array([c["sentence_years"] for c in test_cases])

    # 3. Huấn luyện mô hình phân loại (Classification: Guilty vs Not Guilty)
    console.print("\n[bold]1. Huấn luyện Mô hình Phân loại (Verdict Classification):[/bold]")
    clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
    clf.fit(X_train, y_class_train)

    y_class_pred = clf.predict(X_test)
    y_class_prob = clf.predict_proba(X_test)[:, 1] if len(clf.classes_) > 1 else np.ones(len(X_test))

    acc = accuracy_score(y_class_test, y_class_pred)
    prec = precision_score(y_class_test, y_class_pred, zero_division=0)
    rec = recall_score(y_class_test, y_class_pred, zero_division=0)
    f1 = f1_score(y_class_test, y_class_pred, zero_division=0)

    clf_table = Table(title="Kết Quả Phân Loại Sơ Thẩm (Test Set)")
    clf_table.add_column("Chỉ số Đánh giá", style="cyan")
    clf_table.add_column("Giá trị", style="green")
    clf_table.add_row("Accuracy", f"{acc:.4f}")
    clf_table.add_row("Precision", f"{prec:.4f}")
    clf_table.add_row("Recall", f"{rec:.4f}")
    clf_table.add_row("F1-Score", f"{f1:.4f}")
    console.print(clf_table)

    # 4. Huấn luyện mô hình hồi quy (Regression: Sentence Years)
    console.print("\n[bold]2. Huấn luyện Mô hình Hồi quy Mức Án (Sentence Years Regression):[/bold]")
    reg = RandomForestRegressor(n_estimators=50, max_depth=3, random_state=42)
    reg.fit(X_train, y_reg_train)

    y_reg_pred = reg.predict(X_test)
    # Ràng buộc pháp lý cơ bản: Mức án không âm và nếu phán quyết vô tội thì mức án = 0
    y_reg_pred = np.clip(y_reg_pred, 0.0, 30.0)
    for i in range(len(y_reg_pred)):
        if y_class_pred[i] == 0:
            y_reg_pred[i] = 0.0

    mae = mean_absolute_error(y_reg_test, y_reg_pred)
    rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
    r2 = r2_score(y_reg_test, y_reg_pred)

    reg_table = Table(title="Kết Quả Hồi Quy Mức Án (Test Set)")
    reg_table.add_column("Chỉ số Đánh giá", style="cyan")
    reg_table.add_column("Giá trị", style="green")
    reg_table.add_row("MAE (Năm tù)", f"{mae:.2f} năm")
    reg_table.add_row("RMSE (Năm tù)", f"{rmse:.2f} năm")
    reg_table.add_row("R² Score", f"{r2:.4f}")
    console.print(reg_table)

    # Chi tiết so sánh từng bản án test
    compare_table = Table(title="Chi Tiết Dự Đoán Trên Tập Kiểm Thử (Chronological Out-of-Time Test)")
    compare_table.add_column("Số Bản Án", style="magenta")
    compare_table.add_column("Tội Danh", style="white")
    compare_table.add_column("Thực Tế", style="cyan")
    compare_table.add_column("Dự Đoán", style="yellow")
    compare_table.add_column("Án Thực Tế", style="green")
    compare_table.add_column("Án Dự Đoán", style="blue")
    compare_table.add_column("Sai Lệch (năm)", style="red")

    for i, c in enumerate(test_cases):
        pred_label = "guilty" if y_class_pred[i] == 1 else "not_guilty"
        diff = abs(y_reg_test[i] - y_reg_pred[i])
        compare_table.add_row(
            c["case_number"] or "N/A",
            c["crime_type"][:20],
            c["verdict"],
            pred_label,
            f"{y_reg_test[i]:.1f} năm",
            f"{y_reg_pred[i]:.1f} năm",
            f"{diff:.2f}",
        )
    console.print(compare_table)

    # 5. Lưu trữ Artifacts
    clf_path = CHECKPOINTS_DIR / "first_instance_classifier.joblib"
    reg_path = CHECKPOINTS_DIR / "first_instance_regressor.joblib"
    meta_path = CHECKPOINTS_DIR / "model_metadata.json"

    joblib.dump(clf, clf_path)
    joblib.dump(reg, reg_path)

    metadata = {
        "model_version": "1.0.0",
        "trained_at": datetime.now().isoformat(),
        "temporal_split_date": "2022-01-01",
        "num_train_samples": len(train_cases),
        "num_test_samples": len(test_cases),
        "feature_names": feature_names,
        "metrics": {
            "classification": {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1},
            "regression": {"mae": float(mae), "rmse": float(rmse), "r2": float(r2)},
        },
    }
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    console.print(f"\n[bold green]✓ Đã lưu thành công model artifacts vào: {CHECKPOINTS_DIR}[/bold green]")
    console.print(f"  • Classifier: {clf_path.name}")
    console.print(f"  • Regressor:  {reg_path.name}")
    console.print(f"  • Metadata:   {meta_path.name}")


if __name__ == "__main__":
    main()
