"""Deep verification tests for Temporal Legal Reasoning Engine (Điều 7 BLHS 2015 & Nghị quyết 41/2017/QH14).

Kiểm thử độc lập, chuyên sâu các tình huống pháp lý thời gian phức tạp và nhạy cảm (Edge Cases):
1. Case 1 (Non-retroactivity / Bất hồi tố nguyên tắc chung): Hành vi xảy ra 2016 (BLHS 1999), xét xử 2018 -> Áp dụng BLHS 1999.
2. Case 2 (Retroactive Leniency / Hồi tố quy định có lợi Điều 7 khoản 3): Trộm cắp 1.5 triệu tháng 10/2017, xét xử tháng 03/2018 -> Áp dụng BLHS 2015 & NQ 41/2017/QH14 để không truy cứu TNHS.
3. Case 3 (Continuous / Prolonged crime - Tội phạm liên tục, kéo dài): Bắt đầu 06/2017, kết thúc 03/2018 -> Áp dụng BLHS 2015.
4. Case 4 (Transitional provision tracking): Trích dẫn chính xác Nghị quyết 41/2017/QH14 của Quốc hội.
5. Case 5 (Uncertainty flag when dates missing): Khuyết offense_date -> uncertainty=True, requires_expert_review=True.
"""

from __future__ import annotations

from datetime import date
import pytest

from src.temporal_legal_engine import (
    ContinuousCrimeResult,
    LegalVersionResult,
    RESOLUTION_41_2017_CITATION,
    SelectionBasis,
    TemporalLegalEngine,
    TheftRetroactivityResult,
    TransitionalRulesEngine,
)


@pytest.fixture
def engine() -> TemporalLegalEngine:
    """Fixture khởi tạo TemporalLegalEngine."""
    return TemporalLegalEngine()


@pytest.fixture
def transitional_engine() -> TransitionalRulesEngine:
    """Fixture khởi tạo TransitionalRulesEngine."""
    return TransitionalRulesEngine()


@pytest.fixture
def standard_blhs_versions() -> list[dict]:
    """Danh sách các phiên bản BLHS chuẩn trong hệ thống tư pháp hình sự Việt Nam."""
    return [
        {
            "id": "BLHS_1999",
            "document_number": "15/1999/QH10",
            "effective_from": date(2000, 7, 1),
            "effective_to": date(2017, 12, 31),
            "is_favorable": False,
        },
        {
            "id": "BLHS_2015",
            "document_number": "100/2015/QH13",
            "effective_from": date(2018, 1, 1),
            "effective_to": None,
            "is_favorable": False,
        },
    ]


# ============================================================================
# CASE 1: Non-retroactivity / Bất hồi tố nguyên tắc chung (Khoản 1 Điều 7 BLHS 2015)
# ============================================================================

class TestNonRetroactivityGeneralPrinciple:
    """Case 1: Nguyên tắc bất hồi tố chung theo Khoản 1 Điều 7 BLHS 2015.

    Quy định pháp lý:
    - Khoản 1 Điều 7 BLHS 2015: 'Điều luật được áp dụng đối với một hành vi phạm tội
      là điều luật đang có hiệu lực thi hành tại thời điểm thực hiện hành vi phạm tội.'
    - Tình huống: Hành vi xảy ra năm 2016 (thời kỳ BLHS 1999), xét xử năm 2018.
      Mặc định áp dụng BLHS 1999 (15/1999/QH10) vì không có quy định mới nhẹ hơn.
    """

    def test_offense_2016_judgment_2018_applies_blhs_1999(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """Hành vi xảy ra ngày 15/05/2016, xét xử ngày 20/08/2018 -> Áp dụng BLHS 1999."""
        offense_date = date(2016, 5, 15)
        judgment_date = date(2018, 8, 20)

        result: LegalVersionResult = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=offense_date,
            judgment_date=judgment_date,
        )

        # 1. Phiên bản luật áp dụng phải là BLHS 1999
        assert result.document_id == "BLHS_1999"
        assert result.document_number == "15/1999/QH10"

        # 2. Căn cứ lựa chọn phải là OFFENSE_DATE (thời điểm thực hiện hành vi)
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE

        # 3. Không có sự không chắc chắn (uncertainty=False)
        assert result.uncertainty is False
        assert result.requires_expert_review is False

        # 4. Trích dẫn pháp lý phải viện dẫn Khoản 1 Điều 7 BLHS 2015
        assert any("Khoản 1 Điều 7" in cit for cit in result.citations)
        assert any("15/1999/QH10" in cit for cit in result.citations)

        # 5. Có ghi chú chuyển tiếp cảnh báo xét xử diễn ra ở thời kỳ luật mới
        assert result.transitional_note is not None
        assert "Điều 7 BLHS 2015" in result.transitional_note

    @pytest.mark.parametrize(
        "sample_offense_date",
        [
            date(2005, 3, 10),
            date(2010, 11, 25),
            date(2015, 7, 1),
            date(2016, 12, 31),
        ],
    )
    def test_various_dates_in_blhs_1999_era(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
        sample_offense_date: date,
    ):
        """Mọi hành vi xảy ra trong thời kỳ 01/07/2000 - 31/12/2017 xét xử sau 2018 đều áp dụng BLHS 1999 nếu không có quy định mới nhẹ hơn."""
        result = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=sample_offense_date,
            judgment_date=date(2019, 1, 10),
        )
        assert result.document_id == "BLHS_1999"
        assert result.document_number == "15/1999/QH10"
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE


# ============================================================================
# CASE 2: Retroactive Leniency / Hồi tố quy định có lợi (Điều 7 khoản 3 & NQ 41)
# ============================================================================

class TestRetroactiveLeniencyArticle7Clause3:
    """Case 2: Hồi tố quy định có lợi theo Khoản 3 Điều 7 BLHS 2015 và Nghị quyết 41/2017/QH14.

    Tình huống:
    - Hành vi trộm cắp tài sản 1.500.000đ xảy ra tháng 10/2017 (thời kỳ BLHS 1999 khởi điểm là 500.000đ).
    - Xét xử vào tháng 03/2018 (BLHS 2015 có hiệu lực nâng mức định lượng cấu thành tội lên 2.000.000đ).
    - Theo Điều 7 khoản 3 BLHS 2015 và điểm b khoản 1 Điều 2 NQ 41/2017/QH14:
      Hành vi không cấu thành tội phạm theo luật mới -> áp dụng luật mới có lợi -> không truy cứu TNHS / tuyên không phạm tội.
    """

    def test_theft_1_5_million_version_selection_favorable(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """Kiểm tra việc lựa chọn phiên bản: Tự động nhận diện quy định có lợi khi trộm cắp 1.5 triệu đồng."""
        offense_date = date(2017, 10, 15)
        judgment_date = date(2018, 3, 20)
        stolen_value = 1_500_000.0

        result: LegalVersionResult = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=offense_date,
            judgment_date=judgment_date,
            stolen_value=stolen_value,
            crime_type="trộm cắp tài sản",
        )

        # 1. Phiên bản được chọn phải là BLHS 2015 vì có lợi hơn (nâng mức định lượng)
        assert result.document_id == "BLHS_2015"
        assert result.document_number == "100/2015/QH13"

        # 2. Căn cứ lựa chọn là FAVORABLE
        assert result.selected_version_basis == SelectionBasis.FAVORABLE

        # 3. Trích dẫn đầy đủ Khoản 3 Điều 7 BLHS 2015 và Nghị quyết 41/2017/QH14
        assert any("Khoản 3 Điều 7" in cit for cit in result.citations)
        assert any("41/2017/QH14" in cit for cit in result.citations)

        # 4. Ghi chú chuyển tiếp nêu rõ việc phi tội phạm hóa / không truy cứu TNHS
        assert result.transitional_note is not None
        assert "không truy cứu trách nhiệm hình sự" in result.transitional_note.lower() or "tuyên không phạm tội" in result.transitional_note.lower()

    def test_theft_1_5_million_substantive_evaluation_not_guilty(
        self,
        transitional_engine: TransitionalRulesEngine,
    ):
        """Kiểm tra thẩm định thực chất: Không truy cứu trách nhiệm hình sự / Tuyên không phạm tội."""
        offense_date = date(2017, 10, 15)
        judgment_date = date(2018, 3, 20)
        stolen_value = 1_500_000.0

        eval_res: TheftRetroactivityResult = transitional_engine.evaluate_theft_retroactivity(
            stolen_value=stolen_value,
            offense_date=offense_date,
            judgment_date=judgment_date,
            has_qualifying_circumstances=False,
        )

        # 1. Không cấu thành tội phạm theo luật mới có lợi
        assert eval_res.is_crime is False
        assert eval_res.criminal_prosecution is False

        # 2. Khuyến nghị tuyên án: Không truy cứu TNHS / Tuyên không phạm tội
        assert "không truy cứu trách nhiệm hình sự" in eval_res.verdict_recommendation.lower() or "không phạm tội" in eval_res.verdict_recommendation.lower()

        # 3. Luật áp dụng là BLHS 2015 (100/2015/QH13)
        assert eval_res.applied_law == "BLHS_2015"
        assert eval_res.document_number == "100/2015/QH13"
        assert eval_res.is_favorable is True
        assert eval_res.selection_basis == SelectionBasis.FAVORABLE

        # 4. Ngưỡng định lượng so sánh chính xác
        assert eval_res.old_law_threshold == 500_000.0
        assert eval_res.new_law_threshold == 2_000_000.0

        # 5. Căn cứ pháp lý viện dẫn Điểm b Khoản 1 Điều 2 Nghị quyết 41/2017/QH14
        assert any("Khoản 3 Điều 7" in cit for cit in eval_res.citations)
        assert any("41/2017/QH14" in cit for cit in eval_res.citations)
        assert any("Điểm b Khoản 1 Điều 2" in cit for cit in eval_res.citations)
        assert any("Điều 173" in cit for cit in eval_res.citations)

    def test_theft_contrast_above_2_million_still_crime(
        self,
        transitional_engine: TransitionalRulesEngine,
    ):
        """Trường hợp đối ứng: Trộm cắp 5 triệu đồng tháng 10/2017, xét xử tháng 03/2018 -> Vẫn cấu thành tội phạm."""
        eval_res = transitional_engine.evaluate_theft_retroactivity(
            stolen_value=5_000_000.0,
            offense_date=date(2017, 10, 15),
            judgment_date=date(2018, 3, 20),
            has_qualifying_circumstances=False,
        )
        assert eval_res.is_crime is True
        assert eval_res.criminal_prosecution is True
        assert eval_res.applied_law == "BLHS_2015"
        assert eval_res.is_favorable is True

    def test_theft_contrast_under_500k_never_crime(
        self,
        transitional_engine: TransitionalRulesEngine,
    ):
        """Trường hợp đối ứng: Trộm cắp 300.000đ tháng 10/2017 -> Không cấu thành tội phạm theo cả 2 bộ luật."""
        eval_res = transitional_engine.evaluate_theft_retroactivity(
            stolen_value=300_000.0,
            offense_date=date(2017, 10, 15),
            judgment_date=date(2018, 3, 20),
            has_qualifying_circumstances=False,
        )
        assert eval_res.is_crime is False
        assert eval_res.criminal_prosecution is False


# ============================================================================
# CASE 3: Continuous / Prolonged crime - Tội phạm liên tục, kéo dài
# ============================================================================

class TestContinuousAndProlongedCrime:
    """Case 3: Tội phạm liên tục hoặc kéo dài vắt ngang thời điểm chuyển tiếp luật (01/01/2018).

    Nguyên tắc pháp lý:
    - Tội phạm kéo dài (tàng trữ trái phép vũ khí quân dụng, ma túy...) hoặc tội phạm liên tục (buôn lậu nhiều chuyến...):
      Thời điểm thực hiện hành vi phạm tội để xác định luật áp dụng theo Khoản 1 Điều 7 BLHS 2015 là
      THỜI ĐIỂM HÀNH VI KẾT THÚC / BỊ PHÁT HIỆN, NGĂN CHẶN.
    - Hành vi bắt đầu tháng 06/2017 và kết thúc tháng 03/2018:
      Thời điểm kết thúc (tháng 03/2018) là thời điểm BLHS 2015 đã có hiệu lực thi hành.
      Do đó, luật áp dụng BẮT BUỘC PHẢI LÀ BLHS 2015 (100/2015/QH13).
    """

    def test_illegal_possession_of_military_weapons_straddling_dates(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """Tội tàng trữ vũ khí quân dụng: Bắt đầu 01/06/2017, kết thúc/bị bắt 15/03/2018 -> Áp dụng BLHS 2015."""
        offense_start = date(2017, 6, 1)
        offense_end = date(2018, 3, 15)

        result: LegalVersionResult = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=offense_start,
            offense_end_date=offense_end,
            is_prolonged=True,
            crime_type="tàng trữ trái phép vũ khí quân dụng",
        )

        # 1. Luật áp dụng phải là BLHS 2015 vì kết thúc khi luật mới có hiệu lực
        assert result.document_id == "BLHS_2015"
        assert result.document_number == "100/2015/QH13"

        # 2. Căn cứ lựa chọn là OFFENSE_DATE tính tại thời điểm kết thúc hành vi
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE

        # 3. Khi đã xác định rõ tội phạm kéo dài, không để trạng thái không chắc chắn
        assert result.uncertainty is False
        assert result.requires_expert_review is False

        # 4. Trích dẫn Khoản 1 Điều 7 BLHS 2015
        assert any("Khoản 1 Điều 7" in cit for cit in result.citations)

        # 5. Ghi chú chuyển tiếp ghi rõ lý do áp dụng theo thời điểm kết thúc hành vi
        assert result.transitional_note is not None
        assert "thời điểm kết thúc" in result.transitional_note.lower()

    def test_smuggling_continuous_crime_straddling_dates(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """Tội buôn lậu liên tục: Bắt đầu 20/06/2017, kết thúc 25/03/2018 -> Áp dụng BLHS 2015."""
        offense_start = date(2017, 6, 20)
        offense_end = date(2018, 3, 25)

        result = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=offense_start,
            offense_end_date=offense_end,
            is_continuous=True,
            crime_type="buôn lậu",
        )

        assert result.document_id == "BLHS_2015"
        assert result.document_number == "100/2015/QH13"
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE
        assert result.uncertainty is False

    def test_continuous_crime_substantive_evaluator(
        self,
        transitional_engine: TransitionalRulesEngine,
    ):
        """Kiểm tra hàm đánh giá tội phạm liên tục, kéo dài độc lập trong TransitionalRulesEngine."""
        res: ContinuousCrimeResult = transitional_engine.evaluate_continuous_or_prolonged_crime(
            crime_type="Tàng trữ vũ khí quân dụng",
            offense_start_date=date(2017, 6, 1),
            offense_end_date=date(2018, 3, 15),
        )

        assert res.applied_law == "BLHS_2015"
        assert res.document_number == "100/2015/QH13"
        assert res.selection_basis == SelectionBasis.OFFENSE_DATE
        assert any("Khoản 1 Điều 7" in c for c in res.citations)
        assert any("41/2017/QH14" in c for c in res.citations)
        assert "thời điểm hành vi kết thúc" in res.legal_reasoning

    def test_continuous_crime_ending_before_2018_applies_blhs_1999(
        self,
        transitional_engine: TransitionalRulesEngine,
    ):
        """Tội phạm kéo dài hoàn thành trọn vẹn trong năm 2017 (kết thúc trước 2018) -> Áp dụng BLHS 1999."""
        res = transitional_engine.evaluate_continuous_or_prolonged_crime(
            crime_type="Tàng trữ ma túy",
            offense_start_date=date(2017, 1, 1),
            offense_end_date=date(2017, 12, 15),
        )
        assert res.applied_law == "BLHS_1999"
        assert res.document_number == "15/1999/QH10"


# ============================================================================
# CASE 4: Transitional provision tracking (Nghị quyết 41/2017/QH14)
# ============================================================================

class TestTransitionalProvisionTracking:
    """Case 4: Theo dõi và trích dẫn quy định chuyển tiếp (Nghị quyết 41/2017/QH14 của Quốc hội).

    Kiểm tra xem hệ thống có trả về chính xác trích dẫn Nghị quyết 41/2017/QH14
    về việc thi hành Bộ luật Hình sự số 100/2015/QH13 khi xử lý các vụ án chuyển tiếp giữa hai bộ luật.
    """

    def test_citations_contain_resolution_41_in_transitional_case(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """Hệ thống phải tự động bổ sung trích dẫn Nghị quyết 41/2017/QH14 khi vụ án chuyển tiếp."""
        result = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=date(2016, 5, 20),
            judgment_date=date(2018, 6, 15),
        )

        # Trích dẫn phải chứa đúng tên văn bản Nghị quyết 41/2017/QH14
        assert any("41/2017/QH14" in cit for cit in result.citations)
        assert any(
            "Nghị quyết số 41/2017/QH14 của Quốc hội" in cit
            for cit in result.citations
        )

    def test_transitional_note_contains_resolution_41(
        self,
        engine: TemporalLegalEngine,
    ):
        """Hàm check_transitional_provisions phải trả về trích dẫn Nghị quyết 41/2017/QH14."""
        has_trans, note = engine.check_transitional_provisions(
            document_id="BLHS_2015",
            offense_date=date(2016, 1, 1),
            judgment_date=date(2018, 5, 1),
        )

        assert has_trans is True
        assert note is not None
        assert "41/2017/QH14" in note

    def test_direct_resolution_citation_getter(
        self,
        engine: TemporalLegalEngine,
        transitional_engine: TransitionalRulesEngine,
    ):
        """Kiểm tra phương thức cung cấp trích dẫn chuẩn của Nghị quyết 41."""
        cit_engine = engine.get_transitional_resolution_citation()
        cit_trans = transitional_engine.get_transitional_resolution_citation()

        assert cit_engine == RESOLUTION_41_2017_CITATION
        assert cit_trans == RESOLUTION_41_2017_CITATION
        assert "41/2017/QH14" in cit_engine
        assert "100/2015/QH13" in cit_engine


# ============================================================================
# CASE 5: Uncertainty flag when dates missing
# ============================================================================

class TestUncertaintyFlagWhenDatesMissing:
    """Case 5: Gắn cờ uncertainty khi khuyết thông tin ngày tháng.

    Yêu cầu:
    Khi hồ sơ vụ án khuyết ngày xảy ra hành vi (offense_date=None hoặc không xác định),
    hệ thống phải gắn cờ uncertainty=True và cảnh báo requires_expert_review=True.
    """

    def test_missing_offense_date_flags_uncertainty(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """offense_date=None -> uncertainty=True, requires_expert_review=True, basis=UNKNOWN."""
        result: LegalVersionResult = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=None,
            judgment_date=date(2018, 5, 1),
        )

        assert result.uncertainty is True
        assert result.requires_expert_review is True
        assert result.selected_version_basis == SelectionBasis.UNKNOWN
        assert result.uncertainty_reason is not None
        assert "offense_date" in result.uncertainty_reason

    def test_both_dates_none_flags_uncertainty(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """Cả offense_date và judgment_date đều None -> uncertainty=True."""
        result = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=None,
            judgment_date=None,
        )

        assert result.uncertainty is True
        assert result.requires_expert_review is True
        assert result.selected_version_basis == SelectionBasis.UNKNOWN

    def test_invalid_string_offense_date_flags_uncertainty(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """offense_date là chuỗi sai định dạng -> xử lý an toàn và gắn cờ uncertainty=True."""
        result = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date="ngay-khong-xac-dinh",  # type: ignore[arg-type]
            judgment_date=date(2018, 5, 1),
        )

        assert result.uncertainty is True
        assert result.requires_expert_review is True
        assert result.selected_version_basis == SelectionBasis.UNKNOWN

    def test_missing_offense_date_with_empty_versions(
        self,
        engine: TemporalLegalEngine,
    ):
        """Khuyết cả offense_date lẫn danh sách available_versions."""
        result = engine.select_applicable_version(
            available_versions=[],
            offense_date=None,
        )

        assert result.uncertainty is True
        assert result.requires_expert_review is True
        assert result.selected_version_basis == SelectionBasis.UNKNOWN


# ============================================================================
# EXTRA EDGE CASES: Boundary dates & Transitional precision
# ============================================================================

class TestTemporalBoundaryEdgeCases:
    """Các trường hợp biên đặc thù về ngày chuyển tiếp hiệu lực (31/12/2017 vs 01/01/2018)."""

    def test_exact_last_day_of_blhs_1999(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """Hành vi xảy ra đúng ngày 31/12/2017 (ngày cuối cùng BLHS 1999 có hiệu lực)."""
        result = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=date(2017, 12, 31),
            judgment_date=date(2018, 5, 1),
        )
        assert result.document_id == "BLHS_1999"
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE

    def test_exact_first_day_of_blhs_2015(
        self,
        engine: TemporalLegalEngine,
        standard_blhs_versions: list[dict],
    ):
        """Hành vi xảy ra đúng ngày 01/01/2018 (ngày đầu tiên BLHS 2015 có hiệu lực)."""
        result = engine.select_applicable_version(
            available_versions=standard_blhs_versions,
            offense_date=date(2018, 1, 1),
            judgment_date=date(2018, 5, 1),
        )
        assert result.document_id == "BLHS_2015"
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE
        assert result.uncertainty is False
