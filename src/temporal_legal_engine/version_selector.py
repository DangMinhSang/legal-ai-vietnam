"""
Temporal Legal Engine - Version Selector

Xác định phiên bản văn bản pháp luật áp dụng cho vụ án
dựa trên các mốc thời gian và điều khoản chuyển tiếp.

Nguyên tắc cơ bản (BLHS 2015, Điều 7):
- Áp dụng luật tại thời điểm phạm tội (Khoản 1 Điều 7)
- Cấm hồi tố bất lợi (Khoản 2 Điều 7)
- Ngoại lệ: áp dụng luật mới nếu có lợi cho người phạm tội (Khoản 3 Điều 7)
- Nghị quyết 41/2017/QH14 về thi hành BLHS 2015 trong giai đoạn chuyển tiếp
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from loguru import logger


class SelectionBasis(str, Enum):
    OFFENSE_DATE = "offense_date"         # Luật tại thời điểm phạm tội
    JUDGMENT_DATE = "judgment_date"        # Luật tại thời điểm xét xử
    FAVORABLE = "favorable_to_defendant"  # Áp dụng quy định có lợi hơn
    TRANSITIONAL = "transitional_rule"    # Theo điều khoản chuyển tiếp
    UNKNOWN = "unknown"                    # Chưa xác định được


@dataclass
class LegalVersionResult:
    document_id: str
    document_number: str
    selected_version_basis: SelectionBasis
    effective_from: Optional[date]
    effective_to: Optional[date]
    transitional_note: Optional[str] = None
    uncertainty: bool = False
    uncertainty_reason: Optional[str] = None
    requires_expert_review: bool = False
    citations: list[str] = field(default_factory=list)


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


class TemporalLegalEngine:
    """
    Xác định phiên bản văn bản pháp luật áp dụng cho vụ án
    dựa trên các mốc thời gian và điều khoản chuyển tiếp.

    Nguyên tắc cơ bản (BLHS 2015, Điều 7):
    - Áp dụng luật tại thời điểm phạm tội
    - Ngoại lệ: áp dụng luật mới nếu có lợi cho người phạm tội
    - Áp dụng Nghị quyết 41/2017/QH14 cho các vụ án chuyển tiếp giữa BLHS 1999 và BLHS 2015
    - Đối với tội phạm kéo dài hoặc liên tục: thời điểm phạm tội xác định tại thời điểm hành vi kết thúc

    KHÔNG tự động kết luận luật áp dụng khi:
    - Điều khoản chuyển tiếp phức tạp chưa rõ ràng
    - Nhiều lần sửa đổi trong khoảng thời gian hành vi xảy ra mà chưa xác định được tính chất có lợi
    - Hành vi kéo dài qua nhiều thời kỳ pháp luật mà chưa phân định rõ tính chất liên tục
    """

    KNOWN_TRANSITIONAL_DOCUMENTS: dict[str, str] = {
        "BLHS_2015": "Điều 7 BLHS 2015 quy định áp dụng luật có lợi cho người phạm tội; Nghị quyết 41/2017/QH14 về việc thi hành Bộ luật Hình sự số 100/2015/QH13",
        "100/2015/QH13": "Điều 7 BLHS 2015 quy định áp dụng luật có lợi cho người phạm tội; Nghị quyết 41/2017/QH14 về việc thi hành Bộ luật Hình sự số 100/2015/QH13",
        "BLHS_1999": "Nghị quyết 41/2017/QH14 về việc thi hành Bộ luật Hình sự số 100/2015/QH13 và nguyên tắc áp dụng quy định có lợi",
        "15/1999/QH10": "Nghị quyết 41/2017/QH14 về việc thi hành Bộ luật Hình sự số 100/2015/QH13 và nguyên tắc áp dụng quy định có lợi",
    }

    RESOLUTION_41_CITATION: str = (
        "Nghị quyết số 41/2017/QH14 của Quốc hội về việc thi hành Bộ luật Hình sự số 100/2015/QH13"
    )

    def _find_version_at_date(
        self,
        versions: list[dict[str, Any]],
        target_date: date,
    ) -> Optional[dict[str, Any]]:
        """
        Tìm phiên bản văn bản pháp luật có hiệu lực tại ngày target_date.

        Điều kiện có hiệu lực:
        - effective_from is None hoặc effective_from <= target_date
        - VÀ effective_to is None hoặc target_date <= effective_to

        Args:
            versions: Danh sách các phiên bản văn bản pháp luật.
            target_date: Ngày cần tra cứu hiệu lực.

        Returns:
            Phiên bản phù hợp nhất hoặc None nếu không tìm thấy.
        """
        if not versions or target_date is None:
            return None

        norm_target = _to_date(target_date)
        if norm_target is None:
            return None

        matching: list[dict[str, Any]] = []
        for v in versions:
            eff_from = _to_date(v.get("effective_from"))
            eff_to = _to_date(v.get("effective_to"))

            if eff_from is not None and eff_from > norm_target:
                continue
            if eff_to is not None and norm_target > eff_to:
                continue
            matching.append(v)

        if not matching:
            logger.debug(f"Không tìm thấy phiên bản nào có hiệu lực tại ngày {norm_target}")
            return None

        # Sắp xếp ưu tiên phiên bản có effective_from mới nhất
        matching.sort(
            key=lambda x: (_to_date(x.get("effective_from")) or date.min),
            reverse=True,
        )
        logger.debug(
            f"Tìm thấy {len(matching)} phiên bản tại {norm_target}, "
            f"chọn: id={matching[0].get('id')}"
        )
        return matching[0]

    def check_transitional_provisions(
        self,
        document_id: str,
        offense_date: Optional[date] = None,
        judgment_date: Optional[date] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Kiểm tra và xác định các quy định chuyển tiếp có thể áp dụng.

        Args:
            document_id: Mã định danh văn bản pháp luật.
            offense_date: Ngày xảy ra hành vi phạm tội.
            judgment_date: Ngày xét xử vụ án.

        Returns:
            Tuple (has_transitional, note):
            - has_transitional: True nếu có hoặc có khả năng có điều khoản chuyển tiếp.
            - note: Ghi chú giải thích điều khoản chuyển tiếp.
        """
        notes: list[str] = []

        # 1. Kiểm tra văn bản chuyển tiếp đã biết
        if document_id in self.KNOWN_TRANSITIONAL_DOCUMENTS:
            notes.append(self.KNOWN_TRANSITIONAL_DOCUMENTS[document_id])
        else:
            for k, note_text in self.KNOWN_TRANSITIONAL_DOCUMENTS.items():
                if k.lower() in document_id.lower():
                    notes.append(note_text)
                    break

        # 2. Kiểm tra khoảng cách giữa offense_date và judgment_date
        norm_offense = _to_date(offense_date)
        norm_judgment = _to_date(judgment_date)
        if norm_offense and norm_judgment:
            diff_years = norm_offense.year != norm_judgment.year
            days_apart = abs((norm_judgment - norm_offense).days) > 365
            if diff_years and days_apart:
                notes.append(
                    f"Thời điểm phạm tội ({norm_offense}) và thời điểm xét xử ({norm_judgment}) "
                    "khác năm và cách nhau hơn 365 ngày; có thể có điều khoản chuyển tiếp áp dụng."
                )
            if norm_offense < date(2018, 1, 1) and norm_judgment >= date(2018, 1, 1):
                notes.append(
                    "Vụ án chuyển tiếp giữa thời kỳ BLHS 1999 và BLHS 2015: "
                    "Áp dụng Điều 7 BLHS 2015 và Nghị quyết số 41/2017/QH14 của Quốc hội về việc thi hành BLHS 2015."
                )

        has_transitional = len(notes) > 0
        final_note = "; ".join(notes) if has_transitional else None

        logger.debug(
            f"Transitional check - doc: '{document_id}', offense: {norm_offense}, "
            f"judgment: {norm_judgment} -> has_transitional={has_transitional}, note={final_note}"
        )
        return has_transitional, final_note

    def get_transitional_resolution_citation(self) -> str:
        """Trả về trích dẫn Nghị quyết 41/2017/QH14 của Quốc hội."""
        return self.RESOLUTION_41_CITATION

    def select_applicable_version(
        self,
        document_number: Any = None,
        offense_date: Optional[date] = None,
        judgment_date: Optional[date] = None,
        available_versions: Optional[list[dict[str, Any]]] = None,
        document_id: Optional[str] = None,
        offense_end_date: Optional[date] = None,
        is_continuous: bool = False,
        is_prolonged: bool = False,
        crime_type: Optional[str] = None,
        stolen_value: Optional[float] = None,
        property_value: Optional[float] = None,
        **kwargs: Any,
    ) -> LegalVersionResult:
        """
        Xác định phiên bản văn bản pháp luật áp dụng cho vụ án.
        Supports both (document_number, offense_date, judgment_date, available_versions)
        and (available_versions=..., offense_date=..., etc.)
        """
        # Handle legacy or alternate argument order
        if isinstance(document_number, list):
            available_versions = document_number
            document_number = kwargs.get("document_number")
        if available_versions is None and "available_versions" in kwargs:
            available_versions = kwargs["available_versions"]
        if available_versions is None:
            available_versions = []

        # Case 1: Thiếu offense_date
        norm_offense = _to_date(offense_date)
        if offense_date is None or norm_offense is None:
            logger.warning(
                "Không có thông tin ngày phạm tội (offense_date). "
                "Không thể xác định phiên bản áp dụng chính xác."
            )
            fallback_id = (
                document_id
                or (available_versions[0].get("id", "UNKNOWN") if available_versions else "UNKNOWN")
            )
            fallback_num = (
                document_number
                or (available_versions[0].get("document_number", "UNKNOWN") if available_versions else "UNKNOWN")
            )
            return LegalVersionResult(
                document_id=fallback_id,
                document_number=fallback_num,
                selected_version_basis=SelectionBasis.UNKNOWN,
                effective_from=None,
                effective_to=None,
                uncertainty=True,
                uncertainty_reason="Không có thông tin ngày phạm tội (offense_date)",
                requires_expert_review=True,
                citations=[],
            )

        norm_judgment = _to_date(judgment_date)
        norm_offense_end = _to_date(offense_end_date)

        # Case 2: available_versions rỗng
        if not available_versions:
            logger.error("Danh sách available_versions rỗng. Không có dữ liệu để lựa chọn.")
            return LegalVersionResult(
                document_id=document_id or "UNKNOWN",
                document_number="UNKNOWN",
                selected_version_basis=SelectionBasis.UNKNOWN,
                effective_from=None,
                effective_to=None,
                uncertainty=True,
                uncertainty_reason="Danh sách phiên bản văn bản pháp luật rỗng (không có phiên bản khả dụng)",
                requires_expert_review=True,
                citations=[],
            )

        # Case 3: Tìm tất cả các phiên bản có hiệu lực tại offense_date
        covering_versions: list[dict[str, Any]] = []
        for v in available_versions:
            eff_from = _to_date(v.get("effective_from"))
            eff_to = _to_date(v.get("effective_to"))

            if eff_from is not None and eff_from > norm_offense:
                continue
            if eff_to is not None and norm_offense > eff_to:
                continue
            covering_versions.append(v)

        selected_version: dict[str, Any]
        selected_basis: SelectionBasis
        uncertainty: bool = False
        uncertainty_reason: Optional[str] = None
        requires_expert_review: bool = False
        transitional_notes: list[str] = []

        # Case 4: Không có phiên bản nào bao phủ offense_date
        if not covering_versions:
            prior_versions = [
                v for v in available_versions
                if (_to_date(v.get("effective_from")) is not None and _to_date(v.get("effective_from")) <= norm_offense)
                or (_to_date(v.get("effective_to")) is not None and _to_date(v.get("effective_to")) <= norm_offense)
            ]
            if not prior_versions:
                logger.warning(
                    f"Không có phiên bản nào bao phủ ngày phạm tội ({norm_offense}) "
                    "và không có phiên bản nào trước đó."
                )
                fallback_id = document_id or available_versions[0].get("id", "UNKNOWN")
                fallback_num = available_versions[0].get("document_number", "UNKNOWN")
                return LegalVersionResult(
                    document_id=fallback_id,
                    document_number=fallback_num,
                    selected_version_basis=SelectionBasis.UNKNOWN,
                    effective_from=None,
                    effective_to=None,
                    uncertainty=True,
                    uncertainty_reason=(
                        f"Không tìm thấy phiên bản luật có hiệu lực tại hoặc trước ngày phạm tội ({norm_offense})"
                    ),
                    requires_expert_review=True,
                    citations=[],
                )

            # Chọn phiên bản gần nhất trước offense_date
            prior_versions.sort(
                key=lambda x: (
                    _to_date(x.get("effective_to"))
                    or _to_date(x.get("effective_from"))
                    or date.min
                ),
                reverse=True,
            )
            selected_version = prior_versions[0]
            selected_basis = SelectionBasis.OFFENSE_DATE
            uncertainty = True
            uncertainty_reason = (
                f"Không có phiên bản luật có hiệu lực tại ngày phạm tội ({norm_offense}). "
                f"Tạm chọn phiên bản gần nhất trước đó ({selected_version.get('document_number')})."
            )
            requires_expert_review = True
            logger.warning(
                f"Không có phiên bản bao phủ {norm_offense}. "
                f"Sử dụng phiên bản gần nhất trước đó: {selected_version.get('id')}."
            )

        # Case 5: Đúng 1 phiên bản bao phủ offense_date
        elif len(covering_versions) == 1:
            selected_version = covering_versions[0]
            selected_basis = SelectionBasis.OFFENSE_DATE
            uncertainty = False
            uncertainty_reason = None
            requires_expert_review = False
            logger.debug(
                f"Chỉ có 1 phiên bản có hiệu lực tại ngày phạm tội ({norm_offense}): "
                f"{selected_version.get('id')} ({selected_version.get('document_number')})"
            )

        # Case 6: Nhiều phiên bản cùng bao phủ offense_date
        else:
            covering_versions.sort(
                key=lambda x: (_to_date(x.get("effective_from")) or date.min),
                reverse=True,
            )
            selected_version = covering_versions[0]
            selected_basis = SelectionBasis.OFFENSE_DATE
            uncertainty = True
            uncertainty_reason = "Nhiều phiên bản có hiệu lực tại thời điểm phạm tội"
            requires_expert_review = True
            logger.warning(
                f"Nhiều phiên bản ({len(covering_versions)}) cùng có hiệu lực tại ngày phạm tội ({norm_offense}). "
                "Yêu cầu chuyên gia thẩm định."
            )

        # Kiểm tra hành vi kéo dài / liên tục qua nhiều phiên bản luật (prolonged / continuous offense)
        is_continuous_classified = (
            is_continuous
            or is_prolonged
            or kwargs.get("is_continuous_or_prolonged", False)
            or (
                crime_type is not None
                and any(
                    kw in str(crime_type).lower()
                    for kw in [
                        "tàng trữ",
                        "buôn lậu",
                        "vũ khí",
                        "continuous",
                        "prolonged",
                        "kéo dài",
                        "liên tục",
                    ]
                )
            )
        )

        if norm_offense_end is not None and norm_offense is not None and norm_offense_end > norm_offense:
            end_version = self._find_version_at_date(available_versions, norm_offense_end)
            if end_version and end_version.get("id") != selected_version.get("id"):
                if is_continuous_classified:
                    # Với tội phạm kéo dài hoặc liên tục:
                    # Thời điểm thực hiện hành vi là thời điểm kết thúc hành vi (Khoản 1 Điều 7 BLHS 2015).
                    # Do đó áp dụng phiên bản luật có hiệu lực tại thời điểm kết thúc hành vi.
                    selected_version = end_version
                    selected_basis = SelectionBasis.OFFENSE_DATE
                    uncertainty = False
                    uncertainty_reason = None
                    requires_expert_review = False
                    transitional_notes.append(
                        f"Hành vi phạm tội liên tục/kéo dài ({crime_type or 'tội phạm kéo dài'}) "
                        f"kết thúc vào ngày {norm_offense_end}: Áp dụng phiên bản luật có hiệu lực tại thời điểm "
                        f"kết thúc hành vi ({selected_version.get('document_number')}) "
                        "theo quy định tại Khoản 1 Điều 7 BLHS 2015."
                    )
                else:
                    uncertainty = True
                    uncertainty_reason = "Hành vi kéo dài qua nhiều phiên bản luật khác nhau"
                    requires_expert_review = True

        # Case 7 & 9: Kiểm tra judgment_date và quy định có lợi hơn (Điều 7 BLHS)
        theft_val = stolen_value if stolen_value is not None else property_value
        if theft_val is None and "theft_amount" in kwargs:
            theft_val = kwargs["theft_amount"]

        if norm_judgment is not None:
            # Tìm phiên bản mới hơn có hiệu lực sau phiên bản được chọn và trước/tại judgment_date
            sel_eff_from = _to_date(selected_version.get("effective_from"))
            newer_versions = [
                v for v in available_versions
                if v.get("id") != selected_version.get("id")
                and _to_date(v.get("effective_from")) is not None
                and (
                    (sel_eff_from is not None and _to_date(v["effective_from"]) > sel_eff_from)
                    or _to_date(v["effective_from"]) > norm_offense
                )
                and _to_date(v["effective_from"]) <= norm_judgment
            ]

            # Tự động thẩm định quy định có lợi cho tội trộm cắp nếu có thông tin giá trị tài sản
            is_theft_decriminalized = False
            if (
                theft_val is not None
                and 500_000 <= theft_val < 2_000_000
                and norm_offense < date(2018, 1, 1)
                and norm_judgment >= date(2018, 1, 1)
            ):
                is_theft_decriminalized = True

            # Case 9: Nếu có phiên bản mới hơn có is_favorable=True hoặc tự động thẩm định có lợi
            favorable_newer = [
                v for v in newer_versions
                if v.get("is_favorable", False)
                or (is_theft_decriminalized and ("2015" in str(v.get("id", "")) or "100/2015" in str(v.get("document_number", ""))))
            ]

            if favorable_newer:
                favorable_newer.sort(
                    key=lambda x: (_to_date(x.get("effective_from")) or date.min),
                    reverse=True,
                )
                selected_version = favorable_newer[0]
                selected_basis = SelectionBasis.FAVORABLE
                uncertainty = False
                uncertainty_reason = None
                requires_expert_review = False

                if is_theft_decriminalized:
                    transitional_notes.append(
                        f"Hành vi trộm cắp tài sản giá trị {theft_val:,.0f}đ: Theo Điều 138 BLHS 1999 cấu thành tội phạm "
                        f"(mức khởi điểm 500.000đ), nhưng theo Điều 173 BLHS 2015 không cấu thành tội phạm "
                        f"(mức khởi điểm nâng lên 2.000.000đ). Căn cứ Khoản 3 Điều 7 BLHS 2015 và điểm b khoản 1 "
                        f"Điều 2 Nghị quyết 41/2017/QH14 của Quốc hội, áp dụng quy định có lợi của BLHS 2015: "
                        "không truy cứu trách nhiệm hình sự / tuyên không phạm tội."
                    )
                else:
                    transitional_notes.append(
                        "Áp dụng quy định có lợi hơn cho người phạm tội theo khoản 3 Điều 7 BLHS 2015."
                    )
                logger.debug(
                    f"Áp dụng phiên bản mới có lợi cho người phạm tội: {selected_version.get('id')}"
                )
            elif newer_versions:
                # Case 7: offense_date và judgment_date trải qua các phiên bản khác nhau nhưng chưa có quy định mới nhẹ hơn
                transitional_notes.append(
                    "Thời điểm phạm tội và thời điểm xét xử trải qua các phiên bản luật khác nhau. "
                    "Cần xem xét Điều 7 BLHS 2015 về việc áp dụng quy định có lợi hơn cho người phạm tội."
                )

        # Kiểm tra điều khoản chuyển tiếp qua check_transitional_provisions
        target_doc_id = document_id or selected_version.get("id", "")
        has_trans, trans_check_note = self.check_transitional_provisions(
            document_id=target_doc_id,
            offense_date=norm_offense,
            judgment_date=norm_judgment,
        )
        if has_trans and trans_check_note:
            transitional_notes.append(trans_check_note)

        # Xây dựng danh sách trích dẫn pháp lý (citations)
        citations: list[str] = []
        doc_num = selected_version.get("document_number")
        if doc_num:
            citations.append(f"Văn bản số {doc_num}")

        if selected_basis == SelectionBasis.OFFENSE_DATE:
            citations.append(
                "Khoản 1 Điều 7 BLHS 2015 (áp dụng điều luật đang có hiệu lực thi hành tại thời điểm thực hiện hành vi phạm tội)"
            )
        elif selected_basis == SelectionBasis.FAVORABLE:
            citations.append(
                "Khoản 3 Điều 7 BLHS 2015 (áp dụng quy định có lợi cho người phạm tội)"
            )
        elif selected_basis == SelectionBasis.JUDGMENT_DATE:
            citations.append(
                "Điều 7 BLHS 2015 (áp dụng luật tại thời điểm xét xử)"
            )
        elif selected_basis == SelectionBasis.TRANSITIONAL:
            citations.append("Quy định tại điều khoản chuyển tiếp")

        # Thêm trích dẫn Nghị quyết 41/2017/QH14 cho các vụ án chuyển tiếp giữa BLHS 1999 và BLHS 2015
        is_transitional_case = (
            (norm_offense is not None and norm_offense < date(2018, 1, 1))
            and (
                (norm_judgment is not None and norm_judgment >= date(2018, 1, 1))
                or (norm_offense_end is not None and norm_offense_end >= date(2018, 1, 1))
                or selected_basis == SelectionBasis.FAVORABLE
                or any("100/2015" in str(v.get("document_number", "")) for v in available_versions)
            )
        )
        if is_transitional_case:
            if self.RESOLUTION_41_CITATION not in citations:
                citations.append(self.RESOLUTION_41_CITATION)
            if selected_basis == SelectionBasis.FAVORABLE:
                point_b_cit = (
                    "Điểm b Khoản 1 Điều 2 Nghị quyết 41/2017/QH14 của Quốc hội "
                    "(không xử lý hình sự đối với hành vi phi tội phạm hóa hoặc nâng mức định lượng)"
                )
                if point_b_cit not in citations:
                    citations.append(point_b_cit)

        final_transitional_note = (
            "; ".join(transitional_notes) if transitional_notes else None
        )

        return LegalVersionResult(
            document_id=selected_version.get("id", target_doc_id),
            document_number=selected_version.get("document_number", "UNKNOWN"),
            selected_version_basis=selected_basis,
            effective_from=_to_date(selected_version.get("effective_from")),
            effective_to=_to_date(selected_version.get("effective_to")),
            transitional_note=final_transitional_note,
            uncertainty=uncertainty,
            uncertainty_reason=uncertainty_reason,
            requires_expert_review=requires_expert_review,
            citations=citations,
        )

    # Alias phương thức thuận tiện
    select_version = select_applicable_version

    def evaluate_theft_retroactivity(
        self,
        stolen_value: float,
        offense_date: Any,
        judgment_date: Any,
        has_qualifying_circumstances: bool = False,
    ):
        """Thẩm định hồi tố quy định có lợi cho tội trộm cắp tài sản."""
        from src.temporal_legal_engine.transitional_rules import TransitionalRulesEngine
        return TransitionalRulesEngine.evaluate_theft_retroactivity(
            stolen_value=stolen_value,
            offense_date=offense_date,
            judgment_date=judgment_date,
            has_qualifying_circumstances=has_qualifying_circumstances,
        )

    def evaluate_continuous_or_prolonged_crime(
        self,
        crime_type: str,
        offense_start_date: Any,
        offense_end_date: Any,
        available_versions: Optional[list[dict[str, Any]]] = None,
    ):
        """Xác định luật áp dụng cho tội phạm kéo dài hoặc liên tục."""
        from src.temporal_legal_engine.transitional_rules import TransitionalRulesEngine
        return TransitionalRulesEngine.evaluate_continuous_or_prolonged_crime(
            crime_type=crime_type,
            offense_start_date=offense_start_date,
            offense_end_date=offense_end_date,
            available_versions=available_versions,
        )


# Alias tương thích với các module khác
TemporalVersionSelector = TemporalLegalEngine

__all__ = [
    "LegalVersionResult",
    "SelectionBasis",
    "TemporalLegalEngine",
    "TemporalVersionSelector",
]
