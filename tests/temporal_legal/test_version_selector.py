"""Tests for Temporal Legal Engine and version selector."""

from __future__ import annotations

from datetime import date

from src.temporal_legal_engine.version_selector import (
    SelectionBasis,
    TemporalLegalEngine,
)


class TestTemporalLegalEngine:
    """Tests for TemporalLegalEngine functionality."""

    def test_no_offense_date_requires_expert_review(self):
        """Khi không có ngày phạm tội, phải đánh dấu cần chuyên gia xem xét."""
        engine = TemporalLegalEngine()
        result = engine.select_applicable_version(
            document_number="100/2015/QH13",
            offense_date=None,
            judgment_date=date(2023, 1, 15),
            available_versions=[
                {
                    "id": "blhs_2015",
                    "document_number": "100/2015/QH13",
                    "effective_from": "2018-01-01",
                    "effective_to": None,
                }
            ],
        )
        assert result.uncertainty is True
        assert result.requires_expert_review is True

    def test_offense_before_law_effective(self):
        """Hành vi trước khi luật có hiệu lực - dùng phiên bản cũ tương ứng."""
        engine = TemporalLegalEngine()
        result = engine.select_applicable_version(
            document_number="100/2015/QH13",
            offense_date=date(2014, 5, 20),
            judgment_date=date(2015, 1, 15),
            available_versions=[
                {
                    "id": "blhs_1999",
                    "document_number": "15/1999/QH10",
                    "effective_from": "2000-07-01",
                    "effective_to": "2017-12-31",
                },
                {
                    "id": "blhs_2015",
                    "document_number": "100/2015/QH13",
                    "effective_from": "2018-01-01",
                    "effective_to": None,
                },
            ],
        )
        assert result.document_id == "blhs_1999"
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE

    def test_offense_after_law_effective(self):
        """Hành vi sau khi luật có hiệu lực - dùng phiên bản đó."""
        engine = TemporalLegalEngine()
        result = engine.select_applicable_version(
            document_number="100/2015/QH13",
            offense_date=date(2020, 6, 15),
            judgment_date=date(2021, 1, 15),
            available_versions=[
                {
                    "id": "blhs_1999",
                    "document_number": "15/1999/QH10",
                    "effective_from": "2000-07-01",
                    "effective_to": "2017-12-31",
                },
                {
                    "id": "blhs_2015",
                    "document_number": "100/2015/QH13",
                    "effective_from": "2018-01-01",
                    "effective_to": None,
                },
            ],
        )
        assert result.document_id == "blhs_2015"
        assert result.selected_version_basis == SelectionBasis.OFFENSE_DATE
        assert result.uncertainty is False

    def test_prolonged_offense_across_versions(self):
        """Hành vi kéo dài qua nhiều phiên bản luật → uncertainty."""
        engine = TemporalLegalEngine()
        result = engine.select_applicable_version(
            document_number="100/2015/QH13",
            offense_date=date(2017, 10, 1),
            offense_end_date=date(2018, 5, 1),
            judgment_date=date(2019, 1, 15),
            available_versions=[
                {
                    "id": "blhs_1999",
                    "document_number": "15/1999/QH10",
                    "effective_from": "2000-07-01",
                    "effective_to": "2017-12-31",
                },
                {
                    "id": "blhs_2015",
                    "document_number": "100/2015/QH13",
                    "effective_from": "2018-01-01",
                    "effective_to": None,
                },
            ],
        )
        assert result.uncertainty is True
        assert result.requires_expert_review is True

    def test_favorable_provision_applied(self):
        """Luật mới có lợi hơn cho bị cáo → SelectionBasis.FAVORABLE."""
        engine = TemporalLegalEngine()
        result = engine.select_applicable_version(
            document_number="100/2015/QH13",
            offense_date=date(2017, 3, 10),
            judgment_date=date(2018, 6, 20),
            available_versions=[
                {
                    "id": "blhs_1999",
                    "document_number": "15/1999/QH10",
                    "effective_from": "2000-07-01",
                    "effective_to": "2017-12-31",
                },
                {
                    "id": "blhs_2015",
                    "document_number": "100/2015/QH13",
                    "effective_from": "2018-01-01",
                    "effective_to": None,
                    "is_favorable": True,
                },
            ],
        )
        assert result.selected_version_basis == SelectionBasis.FAVORABLE
        assert result.document_id == "blhs_2015"
