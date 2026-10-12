"""Predictor dự đoán kết quả xét xử phúc thẩm."""

from __future__ import annotations

from typing import Any
from src.appeal_prediction.feature_builder import AppealFeatureBuilder


class AppealPredictor:
    """Dự đoán kết quả kháng cáo: upheld | overturned | modified."""

    def __init__(self, confidence_threshold: float = 0.60) -> None:
        self.confidence_threshold = confidence_threshold
        self.feature_builder = AppealFeatureBuilder()

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """Dự đoán kết quả phúc thẩm từ features."""
        is_protest = features.get("is_prosecution_protest", 0.0)

        # Baseline heuristic: kháng nghị VKS có tỷ lệ sửa/huỷ cao hơn
        if is_protest > 0.5:
            probs = {"upheld": 0.35, "modified": 0.45, "overturned": 0.20}
        else:
            probs = {"upheld": 0.65, "modified": 0.25, "overturned": 0.10}

        predicted = max(probs, key=lambda k: probs[k])
        return {
            "predicted_outcome": predicted,
            "confidence": float(probs[predicted]),
            "probabilities": probs,
            "model_name": "appeal_baseline",
            "model_version": "0.1.0",
        }
