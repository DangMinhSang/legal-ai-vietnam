"""Predictor dự đoán kết quả xét xử sơ thẩm.

Hỗ trợ:
1. Nạp mô hình máy học đã huấn luyện (RandomForestClassifier, GradientBoostingRegressor)
   từ data/models/checkpoints/ nếu có sẵn.
2. Dự đoán xác suất có tội (guilty) vs vô tội (not_guilty) cùng mức án tù dự kiến (năm).
3. Fallback mượt mà sang heuristic rule nếu chưa có file checkpoint.
4. Tuân thủ nguyên tắc không rò rỉ nhãn (No label leakage).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from src.first_instance.feature_builder import FirstInstanceFeatureBuilder

logger = logging.getLogger(__name__)
DEFAULT_CHECKPOINT_DIR = Path(__file__).resolve().parents[2] / "data" / "models" / "checkpoints"


class FirstInstancePredictor:
    """Dự đoán kết quả xét xử sơ thẩm (Verdict & Sentence Length)."""

    def __init__(
        self,
        confidence_threshold: float = 0.65,
        checkpoint_dir: Path | str | None = None,
        load_checkpoints: bool = True,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.feature_builder = FirstInstanceFeatureBuilder()
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else DEFAULT_CHECKPOINT_DIR

        self.classifier: Any = None
        self.regressor: Any = None
        self.feature_names: list[str] = []
        self.model_version: str = "0.1.0"
        self.model_name: str = "first_instance_heuristic_baseline"

        if load_checkpoints:
            self._try_load_checkpoints()

    def _try_load_checkpoints(self) -> None:
        """Thử nạp các mô hình đã huấn luyện từ thư mục checkpoints."""
        clf_file = self.checkpoint_dir / "first_instance_classifier.joblib"
        reg_file = self.checkpoint_dir / "first_instance_regressor.joblib"
        meta_file = self.checkpoint_dir / "model_metadata.json"

        if clf_file.exists() and reg_file.exists() and meta_file.exists():
            try:
                self.classifier = joblib.load(clf_file)
                self.regressor = joblib.load(reg_file)
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                self.feature_names = meta.get("feature_names", [])
                self.model_version = meta.get("model_version", "1.0.0")
                self.model_name = "first_instance_rf_gbr"
                logger.info(
                    "Đã nạp thành công mô hình sơ thẩm từ checkpoints (version: %s, features: %d)",
                    self.model_version,
                    len(self.feature_names),
                )
            except Exception as e:
                logger.warning("Không thể nạp checkpoint mô hình: %s. Dùng heuristic fallback.", e)
                self.classifier = None
                self.regressor = None

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """Dự đoán kết quả xét xử sơ thẩm từ feature dict."""
        agg = features.get("num_aggravating", 0.0)
        mit = features.get("num_mitigating", 0.0)

        # 1. Dự đoán bằng Trained ML Models nếu có sẵn
        if self.classifier is not None and self.feature_names:
            try:
                # Tạo vector đặc trưng theo thứ tự chuẩn
                vec = np.array([[features.get(fname, 0.0) for fname in self.feature_names]])

                # Phân loại tội danh
                if hasattr(self.classifier, "predict_proba"):
                    probs = self.classifier.predict_proba(vec)[0]
                    # Lớp 1 là guilty, lớp 0 là not_guilty
                    prob_guilty = float(probs[1]) if len(probs) > 1 else float(probs[0])
                else:
                    pred_raw = self.classifier.predict(vec)[0]
                    prob_guilty = 1.0 if pred_raw == 1 else 0.0

                predicted_outcome = (
                    "guilty" if prob_guilty >= self.confidence_threshold else "not_guilty"
                )

                # Hồi quy mức án (năm tù)
                if self.regressor is not None:
                    pred_years = float(self.regressor.predict(vec)[0])
                    # Nếu vô tội thì mức án là 0
                    if predicted_outcome == "not_guilty":
                        pred_years = 0.0
                    else:
                        pred_years = max(0.0, min(30.0, pred_years))
                else:
                    pred_years = 3.0 if predicted_outcome == "guilty" else 0.0

                return {
                    "predicted_outcome": predicted_outcome,
                    "confidence": float(
                        prob_guilty if predicted_outcome == "guilty" else 1.0 - prob_guilty
                    ),
                    "probabilities": {
                        "guilty": float(prob_guilty),
                        "not_guilty": float(1.0 - prob_guilty),
                    },
                    "predicted_sentence_years": round(pred_years, 2),
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                }
            except Exception as e:
                logger.error("Lỗi khi dự đoán bằng ML model: %s. Chuyển sang heuristic fallback.", e)

        # 2. Heuristic baseline fallback
        prob_guilty = min(0.95, max(0.1, 0.5 + 0.1 * agg - 0.1 * mit))
        predicted = "guilty" if prob_guilty >= self.confidence_threshold else "not_guilty"
        base_years = max(0.5, 3.0 + 1.5 * agg - 1.0 * mit) if predicted == "guilty" else 0.0

        return {
            "predicted_outcome": predicted,
            "confidence": float(prob_guilty if predicted == "guilty" else 1.0 - prob_guilty),
            "probabilities": {
                "guilty": float(prob_guilty),
                "not_guilty": float(1.0 - prob_guilty),
            },
            "predicted_sentence_years": round(base_years, 2),
            "model_name": "first_instance_baseline",
            "model_version": "0.1.0",
        }
