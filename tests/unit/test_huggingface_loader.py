"""Unit tests cho HuggingFaceLoader module.

Kiểm tra:
- Danh sách dataset hỗ trợ
- Parse ngày tháng an toàn
- Parse HTML thành văn bản thuần
- Ingest tài liệu pháp lý vào database và gọi LegalIndexer
- Xử lý lỗi khi văn bản rỗng hoặc không hợp lệ
"""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.ingestion.huggingface_loader import HuggingFaceLoader
from src.db.models import LegalDocument


class TestHuggingFaceLoader:
    """Tests cho HuggingFaceLoader."""

    def test_list_supported(self):
        """Hệ thống trả về danh sách các dataset được hỗ trợ."""
        supported = HuggingFaceLoader.list_supported()
        assert isinstance(supported, list)
        assert "th1nhng0/vietnamese-legal-documents" in supported
        assert "khanglt0004/vietnamese_legal_chunks" in supported

    def test_parse_date(self):
        """Parse chính xác nhiều định dạng ngày tháng tiếng Việt."""
        loader = HuggingFaceLoader()
        # DD/MM/YYYY
        d1 = loader._parse_date("01/01/2018")
        assert d1 == datetime(2018, 1, 1)

        # YYYY-MM-DD
        d2 = loader._parse_date("2020-05-15")
        assert d2 == datetime(2020, 5, 15)

        # Chuỗi không hợp lệ hoặc None
        assert loader._parse_date(None) is None
        assert loader._parse_date("không xác định") is None

    def test_html_to_text(self):
        """Lọc bỏ toàn bộ thẻ HTML và trích xuất nội dung văn bản."""
        loader = HuggingFaceLoader()
        html = """
        <html>
            <body>
                <h1>Bộ luật Hình sự 2015</h1>
                <p>Điều 168. <b>Tội cướp tài sản</b></p>
                <p>Người nào dùng vũ lực chiếm đoạt tài sản...</p>
            </body>
        </html>
        """
        text = loader._html_to_text(html)
        assert "Bộ luật Hình sự 2015" in text
        assert "Điều 168. Tội cướp tài sản" in text
        assert "<b>" not in text

    @pytest.mark.asyncio
    async def test_ingest_empty_text(self):
        """Văn bản rỗng phải trả về IngestionResult success=False."""
        loader = HuggingFaceLoader()
        res = await loader.ingest_document(
            title="Văn bản rỗng",
            full_text="",
            doc_type="law",
        )
        assert res.success is False
        assert "không có nội dung" in (res.error or "")

    @pytest.mark.asyncio
    async def test_ingest_document_success(self, db_session):
        """Ingest văn bản thành công vào DB và gọi indexer."""
        mock_indexer = MagicMock()
        mock_indexer.index_chunks = AsyncMock(return_value=["chunk-1", "chunk-2"])

        loader = HuggingFaceLoader(indexer=mock_indexer)
        sample_text = (
            "Điều 168. Tội cướp tài sản.\n"
            "1. Người nào dùng vũ lực chiếm đoạt tài sản thì bị phạt tù từ 03 năm đến 10 năm."
        )

        res = await loader.ingest_document(
            title="Bộ luật Hình sự 2015 - Điều 168",
            full_text=sample_text,
            doc_type="law",
            doc_number="100/2015/QH13",
            issuing_body="Quốc hội",
            effective_date=datetime(2018, 1, 1),
            db_session=db_session,
        )

        assert res.success is True
        assert res.document_id is not None
        assert res.document_type == "law"

        # Kiểm tra index_chunks đã được gọi
        assert mock_indexer.index_chunks.called

        # Kiểm tra bản ghi LegalDocument đã được lưu trong DB
        from sqlalchemy import select

        stmt = select(LegalDocument).where(LegalDocument.id == res.document_id)
        result = await db_session.execute(stmt)
        doc = result.scalar_one_or_none()
        assert doc is not None
        assert doc.doc_number == "100/2015/QH13"
        assert doc.title == "Bộ luật Hình sự 2015 - Điều 168"
