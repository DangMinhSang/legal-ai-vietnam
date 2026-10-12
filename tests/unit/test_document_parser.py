"""Unit tests for DocumentParser module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.document_parser.parser import DocumentParser


class TestDocumentParser:
    """Test suite for DocumentParser functionality."""

    def test_parse_txt_file(self, tmp_path: Path):
        """Test parsing plain text file."""
        sample_file = tmp_path / "test.txt"
        sample_text = "Test legal document content. Nhân danh nước Cộng hoà Xã hội Chủ nghĩa Việt Nam."
        sample_file.write_text(sample_text, encoding="utf-8")

        parser = DocumentParser()
        result = parser.parse(sample_file)

        assert result is not None
        assert result.content == sample_text
        assert result.parse_method == "text_extraction"
        assert result.page_count == 1
        assert not result.is_empty
        assert result.title == "test"

    def test_parse_empty_file(self, tmp_path: Path):
        """Test handling empty file - should raise ValueError."""
        sample_file = tmp_path / "empty.txt"
        sample_file.write_text("", encoding="utf-8")

        parser = DocumentParser()
        with pytest.raises(ValueError, match="empty"):
            parser.parse(sample_file)

    def test_unsupported_format(self, tmp_path: Path):
        """Test graceful handling of unsupported format."""
        sample_file = tmp_path / "unsupported.xyz"
        sample_file.write_text("Some text", encoding="utf-8")

        parser = DocumentParser()
        with pytest.raises(ValueError, match="Unsupported"):
            parser.parse(sample_file)

    def test_extract_text_preferred_over_ocr(self, tmp_path: Path):
        """When PDF has text layer, should not use OCR."""
        dummy_pdf = tmp_path / "sample.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 dummy content")

        parser = DocumentParser()

        # Mock pypdf to simulate a PDF with readable text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "BẢN ÁN HÌNH SỰ SƠ THẨM. TAND Quận 1."
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("pypdf.PdfReader", return_value=mock_reader), \
             patch.object(parser, "_run_ocr") as mock_ocr:
            result = parser.parse(dummy_pdf)

            assert "BẢN ÁN" in result.content
            assert result.parse_method == "text_extraction"
            mock_ocr.assert_not_called()
