"""Transitional rules — xử lý điều khoản chuyển tiếp khi luật thay đổi."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional

from src.temporal_legal_engine.version_selector import SelectionBasis


RESOLUTION_41_2017_CITATION = (
    "Nghị quyết số 41/2017/QH14 của Quốc hội về việc thi hành Bộ luật Hình sự số 100/2015/QH13"
)
RESOLUTION_41_ARTICLE_2_CLAUSE_1_POINT_B = (
    "Điểm b Khoản 1 Điều 2 Nghị quyết 41/2017/QH14 của Quốc hội "
    "(không xử lý hình sự đối với hành vi theo BLHS 1999 là tội phạm nhưng theo BLHS 2015 "
    "không cấu thành tội phạm do nâng mức định lượng)"
)
ARTICLE_7_BLHS_2015_CLAUSE_1 = (
    "Khoản 1 Điều 7 BLHS 2015 (áp dụng điều luật đang có hiệu lực thi hành tại thời điểm thực hiện hành vi phạm tội)"
)
ARTICLE_7_BLHS_2015_CLAUSE_3 = (
    "Khoản 3 Điều 7 BLHS 2015 (áp dụng quy định có lợi cho người phạm tội)"
)

BLHS_1999_DOC_NUMBER = "15/1999/QH10"
BLHS_2015_DOC_NUMBER = "100/2015/QH13"
BLHS_2015_EFFECTIVE_DATE = date(2018, 1, 1)

# Định lượng khởi điểm cấu thành tội Trộm cắp tài sản
THEFT_THRESHOLD_BLHS_1999 = 500_000.0   # Điều 138 BLHS 1999: từ 500.000 đồng
THEFT_THRESHOLD_BLHS_2015 = 2_000_000.0 # Điều 173 BLHS 2015: từ 2.000.000 đồng


def _to_date(val: Any) -> Optional[date]:
    """Chuyển đổi an toàn giá trị date / datetime / str sang date."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return date.fromisoformat(val)
        except ValueError:
            return None
    return None


@dataclass
class TheftRetroactivityResult:
    """Kết quả thẩm định hồi tố quy định có lợi đối với tội trộm cắp tài sản."""

    is_crime: bool
    criminal_prosecution: bool
    verdict_recommendation: str
    applied_law: str
    document_number: str
    property_value: float
    old_law_threshold: float
    new_law_threshold: float
    is_favorable: bool
    selection_basis: SelectionBasis
    citations: list[str] = field(default_factory=list)
    legal_reasoning: str = ""


@dataclass
class ContinuousCrimeResult:
    """Kết quả xác định luật áp dụng cho tội phạm liên tục, kéo dài."""

    applied_law: str
    document_number: str
    offense_start_date: date
    offense_end_date: date
    crime_type: str
    selection_basis: SelectionBasis
    citations: list[str] = field(default_factory=list)
    legal_reasoning: str = ""


class TransitionalRulesEngine:
    """Xử lý các quy tắc chuyển tiếp pháp luật theo Điều 7 BLHS 2015 và Nghị quyết 41/2017/QH14.

    Nguyên tắc cốt lõi:
    1. Bất hồi tố nguyên tắc chung (Khoản 1 Điều 7 BLHS 2015): Áp dụng luật có hiệu lực tại thời điểm phạm tội.
    2. Hồi tố quy định có lợi (Khoản 3 Điều 7 BLHS 2015 & Nghị quyết 41/2017/QH14):
       Áp dụng điều luật mới xóa bỏ tội phạm, giảm hình phạt hoặc nâng mức định lượng cấu thành tội phạm.
    3. Tội phạm liên tục / kéo dài:
       Thời điểm hoàn thành hành vi là thời điểm kết thúc hành vi phạm tội. Áp dụng luật có hiệu lực tại thời điểm kết thúc.
    """

    @staticmethod
    def get_transitional_resolution_citation() -> str:
        """Trả về trích dẫn chính xác của Nghị quyết 41/2017/QH14."""
        return RESOLUTION_41_2017_CITATION

    @staticmethod
    def resolve_criminal_retroactivity(
        crime_date: datetime | date,
        old_law_max_penalty: float,
        new_law_max_penalty: float,
    ) -> dict[str, Any]:
        """Áp dụng nguyên tắc có lợi cho người phạm tội (Điều 7 BLHS 2015)."""
        if new_law_max_penalty < old_law_max_penalty:
            return {
                "applied_version": "new",
                "reason": "Luật mới có hình phạt nhẹ hơn — áp dụng hồi tố theo Điều 7 BLHS 2015.",
            }
        return {
            "applied_version": "old",
            "reason": "Luật cũ áp dụng tại thời điểm hành vi xảy ra (nguyên tắc không hồi tố bất lợi).",
        }

    @classmethod
    def evaluate_theft_retroactivity(
        cls,
        stolen_value: float,
        offense_date: Any,
        judgment_date: Any,
        has_qualifying_circumstances: bool = False,
    ) -> TheftRetroactivityResult:
        """Thẩm định hồi tố quy định có lợi cho tội trộm cắp tài sản (Điều 7 Khoản 3 BLHS 2015 & NQ 41/2017/QH14).

        Tình huống:
        - Hành vi trộm cắp xảy ra trong thời kỳ BLHS 1999 (định lượng từ 500.000đ).
        - Xét xử trong thời kỳ BLHS 2015 (định lượng nâng lên 2.000.000đ).
        - Nếu 500.000đ <= stolen_value < 2.000.000đ và không có tiền án tiền sự/tình tiết định tội khác:
          Hành vi không cấu thành tội phạm theo BLHS 2015.
          Áp dụng hồi tố quy định có lợi theo Khoản 3 Điều 7 BLHS 2015 và điểm b khoản 1 Điều 2 NQ 41/2017/QH14:
          -> Không truy cứu trách nhiệm hình sự, tuyên không phạm tội.
        """
        norm_offense = _to_date(offense_date)
        norm_judgment = _to_date(judgment_date)

        is_offense_in_1999 = (
            norm_offense is not None and norm_offense < BLHS_2015_EFFECTIVE_DATE
        )
        is_judgment_in_2015 = (
            norm_judgment is not None and norm_judgment >= BLHS_2015_EFFECTIVE_DATE
        )

        # Trường hợp chuyển tiếp giữa BLHS 1999 và BLHS 2015
        if is_offense_in_1999 and is_judgment_in_2015:
            # Dưới mức định lượng BLHS 1999 (dưới 500.000đ)
            if stolen_value < THEFT_THRESHOLD_BLHS_1999 and not has_qualifying_circumstances:
                return TheftRetroactivityResult(
                    is_crime=False,
                    criminal_prosecution=False,
                    verdict_recommendation="Không cấu thành tội phạm / Không khởi tố",
                    applied_law="BLHS_1999",
                    document_number=BLHS_1999_DOC_NUMBER,
                    property_value=stolen_value,
                    old_law_threshold=THEFT_THRESHOLD_BLHS_1999,
                    new_law_threshold=THEFT_THRESHOLD_BLHS_2015,
                    is_favorable=False,
                    selection_basis=SelectionBasis.OFFENSE_DATE,
                    citations=[f"Văn bản số {BLHS_1999_DOC_NUMBER}", ARTICLE_7_BLHS_2015_CLAUSE_1],
                    legal_reasoning="Giá trị tài sản dưới mức khởi điểm định tội (500.000đ) của cả hai bộ luật.",
                )

            # Trong khoảng [500.000đ, 2.000.000đ): Cấu thành tội theo BLHS 1999 nhưng phi tội phạm hóa theo BLHS 2015
            if (
                THEFT_THRESHOLD_BLHS_1999 <= stolen_value < THEFT_THRESHOLD_BLHS_2015
                and not has_qualifying_circumstances
            ):
                citations = [
                    f"Văn bản số {BLHS_2015_DOC_NUMBER}",
                    ARTICLE_7_BLHS_2015_CLAUSE_3,
                    RESOLUTION_41_2017_CITATION,
                    RESOLUTION_41_ARTICLE_2_CLAUSE_1_POINT_B,
                    "Điều 173 Bộ luật Hình sự 2015 (Tội trộm cắp tài sản)",
                ]
                reasoning = (
                    f"Hành vi trộm cắp tài sản trị giá {stolen_value:,.0f}đ xảy ra ngày {norm_offense} "
                    f"(thời kỳ BLHS 1999, khởi điểm định tội là 500.000đ theo Điều 138). "
                    f"Tại thời điểm xét xử ngày {norm_judgment}, BLHS 2015 đã có hiệu lực nâng mức định lượng "
                    f"cấu thành tội lên 2.000.000đ theo Điều 173. Căn cứ Khoản 3 Điều 7 BLHS 2015 và "
                    f"Điểm b Khoản 1 Điều 2 Nghị quyết 41/2017/QH14 của Quốc hội, áp dụng quy định có lợi "
                    "của BLHS 2015 để không truy cứu trách nhiệm hình sự, tuyên không phạm tội."
                )
                return TheftRetroactivityResult(
                    is_crime=False,
                    criminal_prosecution=False,
                    verdict_recommendation="Không truy cứu trách nhiệm hình sự / Tuyên không phạm tội",
                    applied_law="BLHS_2015",
                    document_number=BLHS_2015_DOC_NUMBER,
                    property_value=stolen_value,
                    old_law_threshold=THEFT_THRESHOLD_BLHS_1999,
                    new_law_threshold=THEFT_THRESHOLD_BLHS_2015,
                    is_favorable=True,
                    selection_basis=SelectionBasis.FAVORABLE,
                    citations=citations,
                    legal_reasoning=reasoning,
                )

            # Từ 2.000.000đ trở lên: Cấu thành tội phạm ở cả hai bộ luật
            citations = [
                f"Văn bản số {BLHS_2015_DOC_NUMBER}",
                ARTICLE_7_BLHS_2015_CLAUSE_3,
                RESOLUTION_41_2017_CITATION,
                "Điều 173 Bộ luật Hình sự 2015",
            ]
            reasoning = (
                f"Hành vi trộm cắp tài sản trị giá {stolen_value:,.0f}đ cấu thành tội phạm ở cả hai bộ luật. "
                "Áp dụng nguyên tắc có lợi theo Khoản 3 Điều 7 BLHS 2015 và Nghị quyết 41/2017/QH14 "
                "để áp dụng các khung hình phạt hoặc điều kiện có lợi hơn."
            )
            return TheftRetroactivityResult(
                is_crime=True,
                criminal_prosecution=True,
                verdict_recommendation="Truy cứu trách nhiệm hình sự theo khung hình phạt có lợi hơn",
                applied_law="BLHS_2015",
                document_number=BLHS_2015_DOC_NUMBER,
                property_value=stolen_value,
                old_law_threshold=THEFT_THRESHOLD_BLHS_1999,
                new_law_threshold=THEFT_THRESHOLD_BLHS_2015,
                is_favorable=True,
                selection_basis=SelectionBasis.FAVORABLE,
                citations=citations,
                legal_reasoning=reasoning,
            )

        # Mặc định theo luật tại thời điểm phạm tội
        doc_num = BLHS_2015_DOC_NUMBER if (norm_offense and norm_offense >= BLHS_2015_EFFECTIVE_DATE) else BLHS_1999_DOC_NUMBER
        threshold = THEFT_THRESHOLD_BLHS_2015 if doc_num == BLHS_2015_DOC_NUMBER else THEFT_THRESHOLD_BLHS_1999
        is_crime = stolen_value >= threshold or has_qualifying_circumstances
        return TheftRetroactivityResult(
            is_crime=is_crime,
            criminal_prosecution=is_crime,
            verdict_recommendation="Truy cứu trách nhiệm hình sự" if is_crime else "Không cấu thành tội phạm",
            applied_law="BLHS_2015" if doc_num == BLHS_2015_DOC_NUMBER else "BLHS_1999",
            document_number=doc_num,
            property_value=stolen_value,
            old_law_threshold=THEFT_THRESHOLD_BLHS_1999,
            new_law_threshold=THEFT_THRESHOLD_BLHS_2015,
            is_favorable=False,
            selection_basis=SelectionBasis.OFFENSE_DATE,
            citations=[f"Văn bản số {doc_num}", ARTICLE_7_BLHS_2015_CLAUSE_1],
            legal_reasoning=f"Áp dụng luật có hiệu lực tại thời điểm phạm tội ({doc_num}).",
        )

    @classmethod
    def evaluate_continuous_or_prolonged_crime(
        cls,
        crime_type: str,
        offense_start_date: Any,
        offense_end_date: Any,
        available_versions: Optional[list[dict[str, Any]]] = None,
    ) -> ContinuousCrimeResult:
        """Xác định luật áp dụng cho tội phạm kéo dài hoặc liên tục (ví dụ: tàng trữ vũ khí quân dụng, buôn lậu).

        Nguyên tắc pháp lý:
        - Tội phạm kéo dài (tàng trữ vũ khí quân dụng, ma túy...) và tội phạm liên tục:
          Thời điểm thực hiện hành vi để xác định luật áp dụng theo Khoản 1 Điều 7 BLHS 2015 là thời điểm
          hành vi phạm tội kết thúc hoặc bị phát hiện, ngăn chặn.
        - Khi hành vi bắt đầu trong thời kỳ BLHS 1999 và kết thúc sau 01/01/2018 (khi BLHS 2015 có hiệu lực):
          Luật áp dụng PHẢI LÀ BLHS 2015 (100/2015/QH13) vì hành vi kết thúc tại thời điểm BLHS 2015 đang có hiệu lực.
        """
        start_d = _to_date(offense_start_date)
        end_d = _to_date(offense_end_date)
        if start_d is None or end_d is None:
            raise ValueError("Cần cung cấp đầy đủ offense_start_date và offense_end_date")

        # Xác định luật áp dụng dựa trên thời điểm kết thúc hành vi
        if end_d >= BLHS_2015_EFFECTIVE_DATE:
            applied_doc = BLHS_2015_DOC_NUMBER
            applied_law = "BLHS_2015"
        else:
            applied_doc = BLHS_1999_DOC_NUMBER
            applied_law = "BLHS_1999"

        citations = [
            f"Văn bản số {applied_doc}",
            ARTICLE_7_BLHS_2015_CLAUSE_1,
        ]

        # Nếu vắt ngang hai thời kỳ luật
        if start_d < BLHS_2015_EFFECTIVE_DATE and end_d >= BLHS_2015_EFFECTIVE_DATE:
            citations.append(RESOLUTION_41_2017_CITATION)
            reasoning = (
                f"Hành vi phạm tội '{crime_type}' bắt đầu từ ngày {start_d} (thời kỳ BLHS 1999) "
                f"và kết thúc/bị phát hiện vào ngày {end_d} (thời kỳ BLHS 2015 đã có hiệu lực thi hành từ 01/01/2018). "
                f"Theo nguyên tắc xác định thời điểm phạm tội đối với tội phạm liên tục, kéo dài và Khoản 1 Điều 7 BLHS 2015, "
                f"điều luật được áp dụng là điều luật đang có hiệu lực tại thời điểm hành vi kết thúc. "
                f"Do đó, luật áp dụng là BLHS 2015 (Văn bản số {applied_doc})."
            )
        else:
            reasoning = (
                f"Hành vi phạm tội '{crime_type}' hoàn thành tại thời điểm {end_d}. "
                f"Áp dụng văn bản số {applied_doc} có hiệu lực tại thời điểm hành vi kết thúc theo Khoản 1 Điều 7 BLHS 2015."
            )

        return ContinuousCrimeResult(
            applied_law=applied_law,
            document_number=applied_doc,
            offense_start_date=start_d,
            offense_end_date=end_d,
            crime_type=crime_type,
            selection_basis=SelectionBasis.OFFENSE_DATE,
            citations=citations,
            legal_reasoning=reasoning,
        )
