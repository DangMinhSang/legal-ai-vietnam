"""Unit tests cho fact_extraction module.

Kiểm tra:
- Pydantic schemas validate đúng và tuân thủ nguyên tắc không bịa dữ liệu
- ExtractedField trạng thái và validation
- CaseFacts default values và nested fields
- DefendantInfo schema validation
- CaseFactExtractor xử lý LLM output, JSON parsing và fallbacks
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock

from src.fact_extraction.schemas import (
    CaseFacts,
    DefendantInfo,
    ExtractedField,
    ExtractionStatus,
    JudgmentOutcomeSchema,
)
from src.fact_extraction.extractor import CaseFactExtractor


class TestExtractedFieldValidation:
    """Tests cho ExtractedField schema và validation rules."""

    def test_missing_status_requires_none_value(self):
        """Trường có status MISSING bắt buộc value phải là None."""
        field = ExtractedField(status=ExtractionStatus.MISSING, value=None)
        assert field.status == ExtractionStatus.MISSING
        assert field.value is None

        with pytest.raises(ValueError, match="Field with missing status must have None value"):
            ExtractedField(status=ExtractionStatus.MISSING, value="Một giá trị nào đó")

    def test_extracted_status_allows_value_and_metadata(self):
        """Trường có status EXTRACTED lưu giữ đầy đủ giá trị, số trang, và độ tin cậy."""
        field = ExtractedField(
            value="Nguyễn Văn A",
            status=ExtractionStatus.EXTRACTED,
            source_page=2,
            source_paragraph="Đoạn 1 phần Mở đầu",
            confidence=0.95,
        )
        assert field.value == "Nguyễn Văn A"
        assert field.status == ExtractionStatus.EXTRACTED
        assert field.source_page == 2
        assert field.confidence == 0.95

    def test_inferred_status_allowed(self):
        """Hệ thống phân biệt rõ giữa EXTRACTED và INFERRED (suy diễn)."""
        field = ExtractedField(
            value="provincial",
            status=ExtractionStatus.INFERRED,
            confidence=0.7,
        )
        assert field.status == ExtractionStatus.INFERRED
        assert field.value == "provincial"

    def test_conflicting_status_allowed(self):
        """Khi có mâu thuẫn trong hồ sơ, trạng thái CONFLICTING được ghi nhận."""
        field = ExtractedField(
            value="15/01/2023 hoặc 15/02/2023",
            status=ExtractionStatus.CONFLICTING,
            confidence=0.5,
        )
        assert field.status == ExtractionStatus.CONFLICTING


class TestCaseFactsSchema:
    """Tests cho CaseFacts aggregate schema."""

    def test_default_case_facts_all_missing(self):
        """Mọi trường chưa được trích xuất đều mặc định là MISSING, không tự suy diễn."""
        facts = CaseFacts()
        assert facts.case_number.status == ExtractionStatus.MISSING
        assert facts.case_number.value is None
        assert facts.court_name.status == ExtractionStatus.MISSING
        assert facts.offense_date.status == ExtractionStatus.MISSING
        assert len(facts.charges) == 0
        assert len(facts.applied_articles) == 0

    def test_populated_case_facts(self):
        """CaseFacts có thể lưu trữ đầy đủ thông tin vụ án."""
        facts = CaseFacts(
            case_number=ExtractedField(value="01/2023/HSST", status=ExtractionStatus.EXTRACTED),
            court_name=ExtractedField(value="TAND Tỉnh Đồng Nai", status=ExtractionStatus.EXTRACTED),
            charges=[
                ExtractedField(value="Tội cướp tài sản", status=ExtractionStatus.EXTRACTED),
            ],
            applied_articles=[
                ExtractedField(value="Điều 168 khoản 1 BLHS 2015", status=ExtractionStatus.EXTRACTED),
            ],
        )
        assert facts.case_number.value == "01/2023/HSST"
        assert len(facts.charges) == 1
        assert facts.charges[0].value == "Tội cướp tài sản"


class TestDefendantInfoSchema:
    """Tests cho DefendantInfo schema."""

    def test_defendant_info_creation(self):
        """Thông tin bị cáo đầy đủ các trường trích xuất."""
        defendant = DefendantInfo(
            name=ExtractedField(value="Nguyễn Văn X", status=ExtractionStatus.EXTRACTED),
            birth_year=ExtractedField(value="1995", status=ExtractionStatus.EXTRACTED),
            sentence_type=ExtractedField(value="tù có thời hạn", status=ExtractionStatus.EXTRACTED),
            sentence_duration=ExtractedField(value="3 năm", status=ExtractionStatus.EXTRACTED),
            sentence_years=ExtractedField(value="3.0", status=ExtractionStatus.EXTRACTED),
        )
        assert defendant.name.value == "Nguyễn Văn X"
        assert defendant.sentence_years.value == "3.0"


class TestJudgmentOutcomeSchema:
    """Tests cho JudgmentOutcomeSchema."""

    def test_outcome_schema_defaults(self):
        outcome = JudgmentOutcomeSchema(
            verdict="co_toi",
            offense_labels=["Tội cướp tài sản"],
            applied_provisions=["Điều 168 khoản 1 BLHS 2015"],
            principal_penalties=["3 năm tù"],
        )
        assert outcome.verdict == "co_toi"
        assert outcome.annotation_status == "unverified"
        assert outcome.suspended_sentence is None


class TestCaseFactExtractor:
    """Tests cho CaseFactExtractor với Mock LLM."""

    def test_split_sections(self):
        """Extractor chia tách đúng các phần cơ bản của bản án."""
        extractor = CaseFactExtractor(llm_service=MagicMock())
        sample_text = """
        TÒA ÁN NHÂN DÂN QUẬN 1
        BẢN ÁN SỐ: 01/2023/HSST
        NHẬN THẤY:
        Ngày 10/10/2022, bị cáo Nguyễn Văn A có hành vi trộm cắp.
        XÉT THẤY:
        Hành vi của bị cáo nguy hiểm cho xã hội.
        QUYẾT ĐỊNH:
        Tuyên bố bị cáo phạm tội trộm cắp tài sản.
        """
        sections = extractor._split_judgment_sections(sample_text)
        assert "header" in sections
        assert "body" in sections
        assert "verdict" in sections

    def test_extract_with_mock_llm(self):
        """Extractor gọi LLM và parse JSON thành CaseFacts."""
        mock_response = json.dumps({
            "case_number": {"value": "05/2023/HSST", "status": "extracted", "confidence": 0.95},
            "court_name": {"value": "TAND Quận 1", "status": "extracted", "confidence": 0.9},
            "charges": [{"value": "Tội trộm cắp tài sản", "status": "extracted", "confidence": 0.9}],
            "defendants": [
                {
                    "name": {"value": "Trần Văn C", "status": "extracted", "confidence": 0.95},
                    "sentence_type": {"value": "tù có thời hạn", "status": "extracted", "confidence": 0.9},
                    "sentence_duration": {"value": "1 năm", "status": "extracted", "confidence": 0.9},
                }
            ]
        })
        mock_llm = MagicMock()
        mock_llm.generate.return_value = mock_response

        extractor = CaseFactExtractor(llm_service=mock_llm)
        facts, defendants = extractor.extract("Bản án mẫu...", judgment_id="test_001")

        assert isinstance(facts, CaseFacts)
        assert facts.case_number.value == "05/2023/HSST"
        assert facts.court_name.value == "TAND Quận 1"
        assert len(defendants) == 1
        assert defendants[0].name.value == "Trần Văn C"

    def test_extract_handles_malformed_llm_json(self):
        """Extractor xử lý an toàn khi LLM trả về văn bản không phải JSON hợp lệ."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Xin lỗi, tôi không thể trích xuất được thông tin này."

        extractor = CaseFactExtractor(llm_service=mock_llm)
        facts, defendants = extractor.extract("Bản án mẫu...", judgment_id="test_002")

        # Hệ thống không crash mà trả về default missing fields
        assert isinstance(facts, CaseFacts)
        assert facts.case_number.status == ExtractionStatus.MISSING
        assert len(defendants) == 0
