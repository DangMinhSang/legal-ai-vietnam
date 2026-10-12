"""Feature builder cho mô hình dự đoán kết quả phúc thẩm (Appellate Outcome Prediction).

Tuân thủ:
1. Không rò rỉ nhãn phúc thẩm (No Appellate Label Leakage):
   - Tuyệt đối loại trừ các trường trong APPELLATE_OUTCOME_FIELDS.
2. Được phép sử dụng kết quả sơ thẩm (first-instance outcome):
   - Vì tại thời điểm phúc thẩm, bản án sơ thẩm đã được tuyên công khai.
3. Trích xuất đặc trưng kháng cáo/kháng nghị:
   - Chủ thể kháng cáo (bị cáo, bị hại, VKS kháng nghị).
   - Nội dung yêu cầu kháng cáo (xin giảm nhẹ, xin án treo, kêu oan, tăng hình phạt, hủy án).
   - Tình tiết mới phát sinh sau sơ thẩm (bồi thường toàn bộ, gia đình bị hại bãi nại, tình tiết mới).
"""

from __future__ import annotations

import re
from typing import Any

from src.db.models import AppealRecord, JudgmentOutcome
from src.validation.leakage import APPELLATE_OUTCOME_FIELDS


class AppealFeatureBuilder:
    """Xây dựng feature vector từ kết quả sơ thẩm và hồ sơ kháng cáo/kháng nghị."""

    def build_features(
        self,
        first_instance_outcome: JudgmentOutcome | dict[str, Any] | None,
        appeal_record: AppealRecord | dict[str, Any],
    ) -> dict[str, float]:
        """Tạo feature dict cho appeal prediction, đảm bảo không rò rỉ nhãn phúc thẩm."""
        # 1. Trích xuất thông tin người kháng cáo & loại kháng cáo
        if isinstance(appeal_record, dict):
            appellant = str(appeal_record.get("appellant", "defendant")).lower()
            appeal_type = str(appeal_record.get("appeal_type", "appeal")).lower()
            grounds_text = str(appeal_record.get("grounds", ""))
        else:
            appellant = (appeal_record.appellant or "defendant").lower()
            appeal_type = (appeal_record.appeal_type or "appeal").lower()
            grounds_text = appeal_record.grounds or ""

        is_defendant = 1.0 if "defendant" in appellant or "bị cáo" in appellant else 0.0
        is_victim = 1.0 if "victim" in appellant or "bị hại" in appellant else 0.0
        is_protest = 1.0 if appeal_type == "protest" or "prosecution" in appellant or "viện kiểm sát" in appellant or "vks" in appellant else 0.0

        # 2. Phân tích nội dung và căn cứ kháng cáo (grounds text)
        g_lower = grounds_text.lower()
        claim_reduction = 1.0 if any(w in g_lower for w in ["giảm nhẹ", "giảm hình phạt", "giảm mức án", "giảm án"]) else 0.0
        claim_suspended = 1.0 if any(w in g_lower for w in ["án treo", "hưởng án treo"]) else 0.0
        claim_exoneration = 1.0 if any(w in g_lower for w in ["kêu oan", "không phạm tội", "vô tội", "không có tội"]) else 0.0
        claim_increase = 1.0 if any(w in g_lower for w in ["tăng nặng", "tăng hình phạt", "quá nhẹ"]) else 0.0
        claim_retrial = 1.0 if any(w in g_lower for w in ["hủy án", "điều tra lại", "xét xử lại", "vi phạm tố tụng"]) else 0.0

        # Tình tiết mới phát sinh sau phiên tòa sơ thẩm
        new_restitution = 1.0 if any(w in g_lower for w in ["đã bồi thường xong", "khắc phục toàn bộ", "bồi thường thêm", "nộp đủ tiền"]) else 0.0
        victim_petition = 1.0 if any(w in g_lower for w in ["bãi nại", "đơn xin giảm nhẹ của bị hại", "xin tha", "rút yêu cầu"]) else 0.0
        new_mitigating = 1.0 if any(w in g_lower for w in ["tình tiết mới", "lập công", "huân chương", "gia đình có công"]) else 0.0
        procedural_violation = 1.0 if any(w in g_lower for w in ["vi phạm nghiêm trọng", "chưa thu thập chứng cứ", "bỏ lọt tội phạm"]) else 0.0

        # 3. Trích xuất thông tin bản án sơ thẩm
        fi_years = 0.0
        fi_is_guilty = 1.0
        fi_is_suspended = 0.0

        if first_instance_outcome is not None:
            if isinstance(first_instance_outcome, dict):
                fi_years = float(first_instance_outcome.get("sentence_years", 0.0))
                fi_outcome = str(first_instance_outcome.get("outcome", "guilty")).lower()
                fi_is_guilty = 1.0 if fi_outcome == "guilty" else 0.0
                fi_is_suspended = 1.0 if first_instance_outcome.get("suspended", False) else 0.0
            else:
                fi_outcome = (first_instance_outcome.outcome or "guilty").lower()
                fi_is_guilty = 1.0 if fi_outcome == "guilty" else 0.0
                meta = first_instance_outcome.meta or {}
                fi_years = float(meta.get("sentence_years", 0.0))
                fi_is_suspended = 1.0 if meta.get("suspended", False) else 0.0

        features: dict[str, float] = {
            "is_defendant_appeal": is_defendant,
            "is_victim_appeal": is_victim,
            "is_prosecution_protest": is_protest,
            "has_grounds": 1.0 if grounds_text.strip() else 0.0,
            "claim_reduction": claim_reduction,
            "claim_suspended": claim_suspended,
            "claim_exoneration": claim_exoneration,
            "claim_increase": claim_increase,
            "claim_retrial": claim_retrial,
            "has_new_restitution": new_restitution,
            "has_victim_forgiveness": victim_petition,
            "has_new_mitigating": new_mitigating,
            "has_procedural_violation": procedural_violation,
            "first_instance_sentence_years": fi_years,
            "first_instance_is_guilty": fi_is_guilty,
            "first_instance_is_suspended": fi_is_suspended,
        }

        # Kiểm tra kiểm soát rò rỉ nhãn kết quả phúc thẩm
        for k in features:
            assert k not in APPELLATE_OUTCOME_FIELDS, f"LỖI RÒ RỈ: Trường {k} là nhãn phúc thẩm!"

        return features
