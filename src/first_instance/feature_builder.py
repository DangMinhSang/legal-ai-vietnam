"""Feature builder cho mô hình dự đoán kết quả sơ thẩm."""

from __future__ import annotations

from typing import Any
import numpy as np

from src.db.models import Case, CaseFact


class FirstInstanceFeatureBuilder:
    """Chuyển đổi Case và CaseFact thành feature vector số học."""

    FACT_TYPE_WEIGHTS = {
        "charge": 1.0,
        "aggravating": 1.5,
        "mitigating": -1.0,
        "evidence": 0.8,
        "damage": 0.5,
    }

    def build_features(self, case: Case, facts: list[CaseFact]) -> dict[str, float]:
        """Tạo feature dict từ thông tin vụ án và tình tiết."""
        features: dict[str, float] = {
            "num_facts": float(len(facts)),
            "num_aggravating": float(sum(1 for f in facts if f.fact_type == "aggravating")),
            "num_mitigating": float(sum(1 for f in facts if f.fact_type == "mitigating")),
            "num_charges": float(sum(1 for f in facts if f.fact_type == "charge")),
            "avg_confidence": float(
                np.mean([f.confidence or 0.5 for f in facts]) if facts else 0.5
            ),
        }
        # Tỷ lệ tăng nặng / giảm nhẹ
        mit = features["num_mitigating"]
        agg = features["num_aggravating"]
        features["aggravating_to_mitigating_ratio"] = agg / (mit + 1e-5)
        return features
