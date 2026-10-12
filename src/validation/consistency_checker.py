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
