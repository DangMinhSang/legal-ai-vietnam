"""Unit tests for Pydantic schemas and ExtractedField validation."""

from __future__ import annotations

import pytest

from src.api.schemas.analysis import AnalysisRequest, AnalysisResult
from src.api.schemas.common import APIResponse, PaginatedResponse
from src.api.schemas.document import DocumentListItem, DocumentUploadResponse
from src.fact_extraction.schemas import CaseFacts, ExtractedField, ExtractionStatus


class TestExtractedField:
    """Test validation rules for ExtractedField."""

    def test_missing_field(self):
        """Field with missing status should have None value."""
        field = ExtractedField(status=ExtractionStatus.MISSING)
        assert field.value is None
        assert field.status == ExtractionStatus.MISSING

        # Attempting to set a value while status is MISSING should raise ValueError
        with pytest.raises(ValueError, match="Field with missing status must have None value"):
            ExtractedField(status=ExtractionStatus.MISSING, value="Không được phép")

    def test_extracted_field_with_source(self):
        """Extracted field should include source page and details."""
        field = ExtractedField(
            value="Nguyễn Văn A",
            status=ExtractionStatus.EXTRACTED,
            source_page=1,
            source_paragraph="Đoạn mở đầu",
            confidence=0.98,
        )
        assert field.value == "Nguyễn Văn A"
        assert field.status == ExtractionStatus.EXTRACTED
        assert field.source_page == 1
        assert field.source_paragraph == "Đoạn mở đầu"
        assert field.confidence == 0.98


class TestCaseFacts:
    """Test validation and default behavior of CaseFacts."""

    def test_all_missing_defaults_to_missing_status(self):
        """All unpopulated fields should default to MISSING status with None value."""
        facts = CaseFacts()
        assert facts.case_number.status == ExtractionStatus.MISSING
        assert facts.case_number.value is None
        assert facts.court_name.status == ExtractionStatus.MISSING
        assert facts.court_name.value is None
        assert facts.court_level.status == ExtractionStatus.MISSING
        assert facts.judgment_date.status == ExtractionStatus.MISSING
        assert facts.proceeding_stage.status == ExtractionStatus.MISSING
        assert facts.offense_date.status == ExtractionStatus.MISSING
        assert facts.offense_end_date.status == ExtractionStatus.MISSING
        assert facts.first_instance_verdict.status == ExtractionStatus.MISSING
        assert facts.charges == []
        assert facts.applied_articles == []


class TestAPISchemas:
    """Test API response wrappers and pagination schemas."""

    def test_api_response_wrapper(self):
        resp = APIResponse[str](success=True, data="payload", message="OK")
        assert resp.success is True
        assert resp.data == "payload"
        assert resp.errors == []

    def test_paginated_response(self):
        resp = PaginatedResponse[int](
            items=[1, 2, 3],
            total=10,
            page=1,
            page_size=3,
            has_next=True,
        )
        assert len(resp.items) == 3
        assert resp.has_next is True
