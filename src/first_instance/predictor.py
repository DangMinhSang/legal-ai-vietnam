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
from src.legal_domains.criminal import (
    CriminalPenaltySystem,
    PrincipalPenaltyType,
    SupplementaryPenaltyType,
    JudicialMeasureType,
)

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

                res = {
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
                res.update(self._enrich_penalty_details(predicted_outcome, pred_years, features))
                return res
            except Exception as e:
                logger.error("Lỗi khi dự đoán bằng ML model: %s. Chuyển sang heuristic fallback.", e)

        # 2. Heuristic baseline fallback
        prob_guilty = min(0.95, max(0.1, 0.5 + 0.1 * agg - 0.1 * mit))
        predicted = "guilty" if prob_guilty >= self.confidence_threshold else "not_guilty"
        base_years = max(0.5, 3.0 + 1.5 * agg - 1.0 * mit) if predicted == "guilty" else 0.0

        res = {
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
        res.update(self._enrich_penalty_details(predicted, base_years, features))
        return res

    def _enrich_penalty_details(
        self,
        outcome: str,
        sentence_years: float,
        features: dict[str, float],
    ) -> dict[str, Any]:
        """Tích hợp hệ thống 7 hình phạt chính và 7 hình phạt bổ sung theo Điều 32 BLHS."""
        if outcome == "not_guilty":
            return {
                "principal_penalty": {
                    "type": "none",
                    "name": "Không áp dụng hình phạt (Tuyên bố Vô tội)",
                    "formatted": "0.0 năm tù (Vô tội)",
                    "is_suspended": False,
                },
                "supplementary_penalties": [],
                "judicial_measures": [],
                "system_penalties_article_32": {
                    "principal_penalties": CriminalPenaltySystem.get_all_principal_penalties(),
                    "supplementary_penalties": CriminalPenaltySystem.get_all_supplementary_penalties(),
                },
            }

        mit = int(features.get("num_mitigating", 0))
        agg = int(features.get("num_aggravating", 0))
        priors = int(features.get("prior_convictions", 0))
        is_recid = bool(features.get("is_recidivist", 0.0))

        # Đánh giá hình phạt chính theo Điều 32
        is_suspended = False
        principal_type = PrincipalPenaltyType.TU_CO_THOI_HAN.value
        principal_name = "5. Tù có thời hạn (Điều 38 BLHS)"
        formatted = f"{sentence_years} năm tù"

        if sentence_years <= 3.0 and priors == 0 and not is_recid and mit >= 2:
            is_suspended = True
            probation = min(5.0, max(1.0, sentence_years * 2.0))
            principal_name = "5. Tù có thời hạn (Điều 38 BLHS) - Cho hưởng Án treo (Điều 65 BLHS)"
            formatted = f"{sentence_years} năm tù (Cho hưởng Án treo, thử thách {probation} năm)"
        elif sentence_years <= 1.0 and mit >= 3 and priors == 0 and not agg:
            principal_type = PrincipalPenaltyType.CAI_TAO_KHONG_GIAM_GIU.value
            principal_name = "3. Cải tạo không giam giữ (Điều 36 BLHS)"
            formatted = f"{sentence_years} năm cải tạo không giam giữ"
        elif sentence_years > 20.0:
            principal_type = PrincipalPenaltyType.TU_CHUNG_THAN.value
            principal_name = "6. Tù chung thân (Điều 39 BLHS)"
            formatted = "Tù chung thân"

        # Đánh giá 7 hình phạt bổ sung
        sup_penalties: list[dict[str, Any]] = []
        if features.get("crime_is_forgery", 0.0) or features.get("is_organized", 0.0):
            sup_penalties.append({
                "type": SupplementaryPenaltyType.CAM_CHUC_VU_HANH_NGHE.value,
                "name": "1. Cấm đảm nhiệm chức vụ, cấm hành nghề hoặc làm công việc nhất định (Điều 41 BLHS)",
                "duration": "01 đến 03 năm",
            })
            sup_penalties.append({
                "type": SupplementaryPenaltyType.PHAT_TIEN_BO_SUNG.value,
                "name": "6. Phạt tiền bổ sung (Khoản 2 Điều 32 & Điều 35 BLHS)",
                "amount": "10.000.000 đến 30.000.000 VNĐ",
            })
        if agg >= 2:
            sup_penalties.append({
                "type": SupplementaryPenaltyType.QUAN_CHE.value,
                "name": "3. Quản chế (Điều 43 BLHS)",
                "duration": "01 năm",
            })

        # Biện pháp tư pháp (Điều 46, 47, 48)
        jud_measures: list[dict[str, Any]] = []
        if features.get("compensation_made", 0.0):
            jud_measures.append({
                "type": JudicialMeasureType.TRA_LAI_BOI_THUONG.value,
                "name": "Ghi nhận việc đã khắc phục hậu quả, bồi thường thiệt hại (Điều 48 BLHS)",
            })
        if features.get("crime_is_forgery", 0.0):
            jud_measures.append({
                "type": JudicialMeasureType.TICH_THU_VAT_TIEN.value,
                "name": "Tịch thu tiêu hủy tài liệu, CCCD giả; tịch thu sung quỹ số tiền thu lợi bất chính (Điều 47 BLHS)",
            })

        return {
            "principal_penalty": {
                "type": principal_type,
                "name": principal_name,
                "sentence_years": sentence_years,
                "formatted": formatted,
                "is_suspended": is_suspended,
            },
            "supplementary_penalties": sup_penalties,
            "judicial_measures": jud_measures,
            "system_penalties_article_32": {
                "principal_penalties": CriminalPenaltySystem.get_all_principal_penalties(),
                "supplementary_penalties": CriminalPenaltySystem.get_all_supplementary_penalties(),
            },
        }
