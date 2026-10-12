"""Consistency checker — kiểm tra tính nhất quán pháp lý và logic đầu ra của hệ thống.

Kiểm tra:
1. Citation validation: điều luật trích dẫn có tồn tại trong QPPL hay không.
2. Prediction logic: cảnh báo nếu dự đoán mâu thuẫn rõ ràng với tình tiết tăng nặng/giảm nhẹ.
3. Temporal consistency: điều luật áp dụng có hiệu lực tại thời điểm phạm tội/xét xử không.
4. Sentence range validation: mức hình phạt dự đoán có nằm trong khung hình phạt luật định không.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConsistencyChecker:
    """Kiểm tra tính nhất quán và hợp lý của kết quả phân tích."""

    def validate_citation(self, citation_text: str, valid_articles: list[str]) -> bool:
        """Kiểm tra điều luật trích dẫn có nằm trong tập điều luật hợp lệ không."""
        if not valid_articles:
            return True
        return any(art in citation_text for art in valid_articles)

    def validate_prediction_logic(
        self,
        outcome: str,
        aggravating_count: int,
        mitigating_count: int,
    ) -> list[str]:
        """Cảnh báo nếu dự đoán mâu thuẫn rõ ràng với tình tiết."""
        warnings: list[str] = []
        if outcome == "not_guilty" and aggravating_count >= 3 and mitigating_count == 0:
            warnings.append(
                "Cảnh báo: Dự đoán 'không có tội' (not_guilty) mâu thuẫn với việc có nhiều tình tiết tăng nặng (>= 3) và không có tình tiết giảm nhẹ."
            )
        if outcome == "guilty" and aggravating_count == 0 and mitigating_count >= 5:
            warnings.append(
                "Lưu ý: Bị cáo có nhiều tình tiết giảm nhẹ (>= 5) và không có tăng nặng, cần xem xét miễn trách nhiệm hình sự hoặc áp dụng hình phạt nhẹ hơn (Điều 54 BLHS)."
            )
        return warnings

    def validate_temporal_consistency(
        self,
        offense_date: Any,
        law_effective_date: Any,
        is_favorable: bool = False,
    ) -> list[str]:
        """Kiểm tra tính nhất quán về thời gian theo Điều 7 BLHS 2015."""
        warnings: list[str] = []
        if offense_date and law_effective_date:
            from datetime import date, datetime

            def to_d(v: Any) -> date | None:
                if isinstance(v, datetime):
                    return v.date()
                if isinstance(v, date):
                    return v
                return None

            off_d = to_d(offense_date)
            law_d = to_d(law_effective_date)
            if off_d and law_d and off_d < law_d and not is_favorable:
                warnings.append(
                    f"Cảnh báo vi phạm nguyên tắc bất hồi tố: Ngày phạm tội ({off_d}) trước ngày luật có hiệu lực ({law_d}) nhưng không áp dụng nguyên tắc có lợi (Điều 7 khoản 3 BLHS 2015)."
                )
        return warnings

    def validate_sentence_range(
        self,
        predicted_years: float,
        min_years: float,
        max_years: float,
    ) -> list[str]:
        """Kiểm tra mức án dự đoán có nằm trong khung hình phạt luật định không."""
        warnings: list[str] = []
        if predicted_years < min_years:
            warnings.append(
                f"Mức án dự đoán ({predicted_years} năm) thấp hơn mức tối thiểu của khung hình phạt ({min_years} năm). Cần điều kiện áp dụng Điều 54 BLHS (hình phạt dưới mức thấp nhất của khung)."
            )
        elif predicted_years > max_years:
            warnings.append(
                f"Cảnh báo nghiêm trọng: Mức án dự đoán ({predicted_years} năm) vượt quá mức tối đa của khung hình phạt ({max_years} năm)."
            )
        return warnings

    def validate_penalties_consistency(
        self,
        principal_penalty_code: str,
        supplementary_penalty_codes: list[str],
        age: int = 25,
        is_pregnant_or_nursing: bool = False,
        is_foreigner: bool = False,
        sentence_years: float = 0.0,
        is_suspended: bool = False,
    ) -> list[str]:
        """Kiểm tra tính hợp hiến, hợp pháp của hình phạt theo Điều 32, Điều 40 và Chương XII BLHS 2015."""
        warnings: list[str] = []

        # 1. Điều 32 Khoản 2 điểm e, g: Không áp dụng trùng phạt tiền/trục xuất vừa là hình phạt chính vừa là bổ sung
        if principal_penalty_code == "phat_tien" and "phat_tien_bo_sung" in supplementary_penalty_codes:
            warnings.append(
                "Vi phạm Điều 32 Khoản 2 Điểm e BLHS 2015: Phạt tiền chỉ được áp dụng là hình phạt bổ sung khi KHÔNG áp dụng là hình phạt chính."
            )

        if principal_penalty_code == "truc_xuat" and "truc_xuat_bo_sung" in supplementary_penalty_codes:
            warnings.append(
                "Vi phạm Điều 32 Khoản 2 Điểm g BLHS 2015: Trục xuất chỉ được áp dụng là hình phạt bổ sung khi KHÔNG áp dụng là hình phạt chính."
            )

        # 2. Điều 37: Trục xuất chỉ áp dụng cho người nước ngoài
        if (principal_penalty_code == "truc_xuat" or "truc_xuat_bo_sung" in supplementary_penalty_codes) and not is_foreigner:
            warnings.append(
                "Vi phạm Điều 37 BLHS 2015: Hình phạt Trục xuất chỉ áp dụng đối với người nước ngoài hoặc người không quốc tịch."
            )

        # 3. Điều 40: Điều kiện không áp dụng hình phạt Tử hình
        if principal_penalty_code == "tu_hinh":
            if age < 18:
                warnings.append(
                    f"Vi phạm nghiêm trọng Điều 40 Khoản 2 & Điều 98 BLHS: Tuyệt đối không áp dụng hình phạt Tử hình đối với người dưới 18 tuổi khi phạm tội (tuổi hiện tại: {age})."
                )
            if is_pregnant_or_nursing:
                warnings.append(
                    "Vi phạm nghiêm trọng Điều 40 Khoản 2 BLHS: Tuyệt đối không áp dụng hình phạt Tử hình đối với phụ nữ có thai hoặc phụ nữ đang nuôi con dưới 36 tháng tuổi."
                )
            if age >= 75:
                warnings.append(
                    f"Vi phạm Điều 40 Khoản 2 BLHS: Không áp dụng hình phạt Tử hình đối với người đủ 75 tuổi trở lên khi phạm tội hoặc khi xét xử (tuổi: {age})."
                )

        # 4. Điều 39 & Điều 98: Không áp dụng Tù chung thân với người dưới 18 tuổi
        if principal_penalty_code == "tu_chung_than" and age < 18:
            warnings.append(
                f"Vi phạm Điều 39 & Điều 98 BLHS: Không áp dụng hình phạt Tù chung thân đối với người dưới 18 tuổi phạm tội (tuổi: {age})."
            )

        # 5. Điều 65: Án treo chỉ áp dụng khi hình phạt tù không quá 03 năm
        if is_suspended and sentence_years > 3.0:
            warnings.append(
                f"Vi phạm Điều 65 Khoản 1 BLHS: Án treo chỉ được áp dụng khi mức hình phạt tù không quá 03 năm (mức án hiện tại: {sentence_years} năm)."
            )

        return warnings
