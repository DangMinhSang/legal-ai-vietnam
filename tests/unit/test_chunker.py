"""Unit tests cho legal_rag chunker module.

Kiểm tra:
- Chunking theo cấu trúc điều/khoản Việt Nam
- Đảm bảo chunk overlap hoạt động đúng
- Không tạo chunk dưới min_chunk_size
- Giữ nguyên nội dung sau khi join lại các chunk
"""

from __future__ import annotations

import pytest

from src.services.text_chunker import LegalChunker, TextChunkResult


class TestLegalChunker:
    """Tests cho LegalChunker."""

    def test_chunk_by_article_separator(self):
        """Văn bản có 'Điều X.' phải được tách tại ranh giới điều."""
        chunker = LegalChunker(target_chunk_size=512, overlap=64)
        text = (
            "Điều 1. Phạm vi điều chỉnh\n"
            "Luật này quy định về xử lý tội phạm.\n"
            "Điều 2. Đối tượng áp dụng\n"
            "Luật này áp dụng đối với cá nhân và tổ chức."
        )
        chunks = chunker.chunk_legal_document(text)
        assert len(chunks) == 2
        assert chunks[0].legal_ref == "Điều 1"
        assert chunks[0].chunk_type == "article"
        assert chunks[1].legal_ref == "Điều 2"
        assert chunks[1].chunk_type == "article"

    def test_chunk_overlap_preserved(self):
        """Chunk kế tiếp phải chứa phần cuối của chunk trước (overlap)."""
        chunker = LegalChunker(target_chunk_size=512, overlap=64)
        text = (
            "Điều 1. Phạm vi điều chỉnh\n"
            "Nội dung điều một có độ dài tương đối để tạo phần overlap ở phía cuối.\n"
            "Điều 2. Đối tượng áp dụng\n"
            "Nội dung điều hai."
        )
        chunks = chunker.chunk_legal_document(text)
        assert len(chunks) >= 2
        overlap_len = min(64, chunks[0].end_char - chunks[0].start_char)
        prev_tail = text[chunks[0].start_char : chunks[0].end_char][-overlap_len:]
        assert chunks[1].content.startswith(prev_tail)

    def test_min_chunk_size_filter(self):
        """Chunk ngắn hơn min_chunk_size phải bị loại bỏ."""
        chunker = LegalChunker(target_chunk_size=512, overlap=0, min_chunk_size=50)
        text = (
            "Điều 1. Ngắn.\n"
            "Điều 2. Đây là điều số hai có nội dung dài hơn năm mươi ký tự để không bị loại bỏ bởi bộ lọc kích thước tối thiểu."
        )
        chunks = chunker.chunk_legal_document(text, min_chunk_size=50)
        for chunk in chunks:
            assert len(chunk.content.strip()) >= 50 or (chunk.end_char - chunk.start_char) >= 50

    def test_content_preserved_after_chunking(self):
        """Ghép tất cả chunks lại phải khôi phục được nội dung gốc (trừ overlap)."""
        chunker = LegalChunker(target_chunk_size=120, overlap=30)
        text = (
            "Điều 1. Đây là đoạn thứ nhất của điều một dùng để kiểm thử tính nguyên vẹn của văn bản sau khi phân tách.\n"
            "Điều 2. Đây là đoạn thứ hai của điều hai tiếp nối nội dung để đảm bảo không mất mát ký tự nào."
        )
        chunks = chunker.chunk_legal_document(text)
        reconstructed = "".join(text[c.start_char : c.end_char] for c in chunks)
        assert reconstructed == text

    def test_empty_text_returns_no_chunks(self):
        """Văn bản rỗng phải trả về list rỗng."""
        chunker = LegalChunker()
        assert chunker.chunk_legal_document("") == []
        assert chunker.chunk_legal_document("   \n\t  ") == []

    def test_short_text_returns_single_chunk(self):
        """Văn bản ngắn hơn chunk_size phải trả về đúng 1 chunk."""
        chunker = LegalChunker(target_chunk_size=512)
        text = "Văn bản ngắn không có điều khoản đặc biệt."
        chunks = chunker.chunk_legal_document(text)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].content == text
        assert chunks[0].start_char == 0
        assert chunks[0].end_char == len(text)

    def test_vietnamese_separators_recognised(self):
        """Separator 'Chương', 'Mục', 'Điều' tiếng Việt phải được nhận diện."""
        chunker = LegalChunker(target_chunk_size=512)
        text = (
            "Chương I\nQUY ĐỊNH CHUNG\n"
            "Mục 1\nPHẠM VI\n"
            "Điều 1. Phạm vi điều chỉnh\nNội dung điều 1."
        )
        chunks = chunker.chunk_legal_document(text)
        assert len(chunks) >= 3
        types = [c.chunk_type for c in chunks]
        assert "section" in types
        assert "article" in types

    def test_chunk_index_sequential(self):
        """chunk_index phải tăng dần liên tục từ 0."""
        chunker = LegalChunker(target_chunk_size=80, overlap=10)
        text = (
            "Điều 1. Nội dung điều một tương đối dài.\n"
            "Điều 2. Nội dung điều hai tương đối dài.\n"
            "Điều 3. Nội dung điều ba tương đối dài."
        )
        chunks = chunker.chunk_legal_document(text)
        assert len(chunks) >= 3
        for idx, chunk in enumerate(chunks):
            assert chunk.chunk_index == idx
