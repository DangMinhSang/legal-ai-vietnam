"""Unit tests cho TemporalLegalEngine (version_selector.py)."""

from __future__ import annotations

from datetime import date, datetime
import pytest

from src.temporal_legal_engine.version_selector import (
    LegalVersionResult,
    SelectionBasis,
    TemporalLegalEngine,
    TemporalVersionSelector,
)


class TestTemporalLegalEngineUnit:
    """Kiểm tra các trường hợp nghiệp vụ của TemporalLegalEngine."""

    @pytest.fixture
    def engine(self) -> TemporalLegalEngine:
        return TemporalLegalEngine()

    def test_case_1_no_offense_date(self, engine: TemporalLegalEngine):
        """Case 1: Không có offense_date -> uncertainty=True, requires_expert_review=True, basis=UNKNOWN."""
        versions = [
            {"id": "v1", "document_number": "100/2015/QH13", "effective_from": date(2018, 1, 1), "effective_to": None}
        ]
        result = engine.select_applicable_version(available_versions=versions, offense_date=None)
        assert result.uncertainty is True
        assert result.requires_expert_review is True
        assert result.selected_version_basis == SelectionBasis.UNKNOWN
        assert result.document_id == "v1"
        assert result.document_number == "100/2015/QH13"
        assert "offense_date" in result.uncertainty_reason

    def test_case_2_no_available_versions(self, engine: TemporalLegalEngine):
        """Case 2: available_versions rỗng -> uncertainty=True, requires_expert_review=True, log error."""
        result = engine.select_applicable_version(available_versions=[], offense_date=date(2020, 1, 1))
        assert result.uncertainty is True
        assert result.requires_expert_review is True
        assert result.selected_version_basis == SelectionBasis.UNKNOWN
        assert "rỗng" in result.uncertainty_reason

    def test_case_3_and_5_single_matching_version(self, engine: TemporalLegalEngine):
        """Case 3 & 5: Đúng 1 phiên bản bao phủ offense_date -> basis=OFFENSE_DATE, no uncertainty."""
        versions = [
            {
                "id": "blhs_2015",
                "document_number": "100/2015/QH13",
                "effective_from": date(2018, 1, 1),
                "effective_to": None,
            }
        ]
        result = engine.select_applicable_version(available_versions=versions, offense_date=date(2020, 5, 10))
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE
        assert result.uncertainty is False
        assert result.uncertainty_reason is None
        assert result.requires_expert_review is False
        assert result.document_id == "blhs_2015"
        assert result.document_number == "100/2015/QH13"
        assert len(result.citations) > 0

    def test_case_4_no_version_covers_but_prior_exists(self, engine: TemporalLegalEngine):
        """Case 4: Không có phiên bản bao phủ nhưng có phiên bản trước đó -> chọn phiên bản gần nhất trước đó."""
        versions = [
            {
                "id": "v1999",
                "document_number": "15/1999/QH10",
                "effective_from": date(2000, 7, 1),
                "effective_to": date(2017, 12, 31),
            }
        ]
        # Offense date is after v1999 expired, but before any new law
        result = engine.select_applicable_version(available_versions=versions, offense_date=date(2018, 5, 1))
        assert result.document_id == "v1999"
        assert result.uncertainty is True
        assert result.requires_expert_review is True
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE

    def test_case_4_no_version_at_all(self, engine: TemporalLegalEngine):
        """Case 4: Không có phiên bản bao phủ và không có phiên bản trước đó."""
        versions = [
            {
                "id": "v_future",
                "document_number": "200/2026/QH15",
                "effective_from": date(2026, 1, 1),
                "effective_to": None,
            }
        ]
        result = engine.select_applicable_version(available_versions=versions, offense_date=date(2015, 1, 1))
        assert result.selected_version_basis == SelectionBasis.UNKNOWN
        assert result.uncertainty is True
        assert result.requires_expert_review is True

    def test_case_6_multiple_covering_versions(self, engine: TemporalLegalEngine):
        """Case 6: Nhiều phiên bản cùng bao phủ offense_date -> uncertainty=True, requires_expert_review=True."""
        versions = [
            {
                "id": "v_goc",
                "document_number": "100/2015/QH13",
                "effective_from": date(2018, 1, 1),
                "effective_to": date(2025, 1, 1),
            },
            {
                "id": "v_sua_doi",
                "document_number": "12/2017/QH14",
                "effective_from": date(2018, 1, 1),
                "effective_to": date(2025, 1, 1),
            },
        ]
        result = engine.select_applicable_version(available_versions=versions, offense_date=date(2020, 1, 1))
        assert result.uncertainty is True
        assert result.uncertainty_reason == "Nhiều phiên bản có hiệu lực tại thời điểm phạm tội"
        assert result.requires_expert_review is True

    def test_case_7_different_versions_span_without_favorable(self, engine: TemporalLegalEngine):
        """Case 7: offense_date và judgment_date trải qua nhiều phiên bản -> ghi chú Điều 7 BLHS."""
        versions = [
            {
                "id": "v_old",
                "document_number": "15/1999/QH10",
                "effective_from": date(2000, 7, 1),
                "effective_to": date(2017, 12, 31),
                "is_favorable": False,
            },
            {
                "id": "v_new",
                "document_number": "100/2015/QH13",
                "effective_from": date(2018, 1, 1),
                "effective_to": None,
                "is_favorable": False,
            },
        ]
        result = engine.select_applicable_version(
            available_versions=versions,
            offense_date=date(2015, 6, 1),
            judgment_date=date(2019, 6, 1),
        )
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE
        assert result.document_id == "v_old"
        assert result.transitional_note is not None
        assert "Điều 7 BLHS 2015" in result.transitional_note

    def test_case_9_favorable_newer_version(self, engine: TemporalLegalEngine):
        """Case 9: Phiên bản mới hơn có is_favorable=True và có judgment_date -> SelectionBasis.FAVORABLE."""
        versions = [
            {
                "id": "v_old",
                "document_number": "15/1999/QH10",
                "effective_from": date(2000, 7, 1),
                "effective_to": date(2017, 12, 31),
                "is_favorable": False,
            },
            {
                "id": "v_new",
                "document_number": "100/2015/QH13",
                "effective_from": date(2018, 1, 1),
                "effective_to": None,
                "is_favorable": True,
            },
        ]
        result = engine.select_applicable_version(
            available_versions=versions,
            offense_date=date(2016, 1, 1),
            judgment_date=date(2018, 6, 1),
        )
        assert result.selected_version_basis == SelectionBasis.FAVORABLE
        assert result.document_id == "v_new"
        assert result.uncertainty is False
        assert any("Khoản 3 Điều 7" in c for c in result.citations)

    def test_transitional_provisions_check(self, engine: TemporalLegalEngine):
        """Kiểm tra logic check_transitional_provisions."""
        # Known document
        has_trans, note = engine.check_transitional_provisions("BLHS_2015")
        assert has_trans is True
        assert "Điều 7 BLHS 2015" in note

        # Different years and > 365 days
        has_trans2, note2 = engine.check_transitional_provisions(
            "DOC_OTHER",
            offense_date=date(2020, 1, 1),
            judgment_date=date(2022, 6, 1),
        )
        assert has_trans2 is True
        assert "365 ngày" in note2

        # Same year
        has_trans3, note3 = engine.check_transitional_provisions(
            "DOC_OTHER",
            offense_date=date(2020, 1, 1),
            judgment_date=date(2020, 6, 1),
        )
        assert has_trans3 is False
        assert note3 is None

    def test_find_version_at_date(self, engine: TemporalLegalEngine):
        """Kiểm tra helper _find_version_at_date."""
        versions = [
            {"id": "v1", "effective_from": date(2010, 1, 1), "effective_to": date(2015, 12, 31)},
            {"id": "v2", "effective_from": date(2016, 1, 1), "effective_to": date(2020, 12, 31)},
        ]
        v = engine._find_version_at_date(versions, date(2018, 5, 1))
        assert v is not None
        assert v["id"] == "v2"

        v_none = engine._find_version_at_date(versions, date(2025, 1, 1))
        assert v_none is None

    def test_alias_equivalence(self):
        """Đảm bảo TemporalVersionSelector trỏ tới TemporalLegalEngine."""
        assert TemporalVersionSelector is TemporalLegalEngine
