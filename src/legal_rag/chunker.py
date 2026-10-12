"""Legal chunker — phân đoạn văn bản pháp luật Việt Nam.

Chiến lược chunking dựa trên cấu trúc văn bản pháp luật:
- Ưu tiên tách tại ranh giới Điều, Chương, Mục
- Hỗ trợ overlap giữa các chunk kế tiếp
- Bỏ qua các chunk ngắn hơn min_chunk_size
- Giữ nguyên metadata số điều trong từng chunk
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Separators theo thứ tự ưu tiên cho văn bản pháp luật Việt Nam
LEGAL_SEPARATORS = [
    r"\n(?=(?:Điều|ĐIỀU)\s+\d+)",       # Ranh giới Điều
    r"\n(?=(?:Chương|CHƯƠNG)\s+[IVXLCDM\d]+)",  # Ranh giới Chương
    r"\n(?=(?:Mục|MỤC)\s+\d+)",         # Ranh giới Mục
    r"\n\n",                             # Đoạn văn
    r"\n",                               # Dòng
    r" ",                                # Từ
]


@dataclass
class Chunk:
    """Một đoạn văn bản đã được chunk."""

    content: str
    chunk_index: int
    char_start: int
    char_end: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def length(self) -> int:
        return len(self.content)

    @property
    def word_count(self) -> int:
        return len(self.content.split())


class LegalChunker:
    """Chunker chuyên biệt cho văn bản pháp luật Việt Nam.

    Sử dụng:
        chunker = LegalChunker(chunk_size=1000, chunk_overlap=100)
        chunks = chunker.chunk(full_text, metadata={"doc_id": "123"})
    """

    def __init__(
        self,
        chunk_size: int = 1000,        # Ký tự xấp xỉ
        chunk_overlap: int = 150,      # Ký tự overlap
        min_chunk_size: int = 100,     # Bỏ chunk nhỏ hơn giá trị này
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Chia văn bản thành danh sách Chunk.

        Args:
            text: Văn bản toàn văn cần chunk
            metadata: Metadata dùng chung cho tất cả chunk (doc_id, title, ...)

        Returns:
            Danh sách Chunk có thứ tự
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        base_meta = metadata or {}

        # Nếu văn bản ngắn hơn chunk_size, trả về 1 chunk duy nhất
        if len(text) <= self.chunk_size:
            return [
                Chunk(
                    content=text,
                    chunk_index=0,
                    char_start=0,
                    char_end=len(text),
                    metadata=base_meta.copy(),
                )
            ]

        # Tách theo Điều trước tiên
        splits = re.split(r"\n(?=(?:Điều|ĐIỀU)\s+\d+)", text)
        if len(splits) > 1:
            raw_chunks = splits
        else:
            # Fallback: tách theo đoạn văn
            raw_chunks = text.split("\n\n")

        # Gom các đoạn nhỏ và cắt các đoạn lớn
        merged: list[str] = []
        current = ""

        for part in raw_chunks:
            part = part.strip()
            if not part:
                continue

            if len(current) + len(part) + 1 <= self.chunk_size:
                current = f"{current}\n\n{part}".strip()
            else:
                if current and len(current) >= self.min_chunk_size:
                    merged.append(current)
                # Nếu part tự thân quá dài, cắt theo ký tự
                if len(part) > self.chunk_size:
                    sub_parts = self._split_fixed(part)
                    merged.extend(sub_parts[:-1])
                    current = sub_parts[-1] if sub_parts else ""
                else:
                    current = part

        if current and len(current) >= self.min_chunk_size:
            merged.append(current)

        # Tạo đối tượng Chunk với overlap và metadata
        chunks: list[Chunk] = []
        pos = 0
        for idx, content in enumerate(merged):
            chunk_meta = base_meta.copy()
            # Trích xuất số điều nếu có
            article_match = re.search(r"(?:Điều|ĐIỀU)\s+(\d+)", content)
            if article_match:
                chunk_meta["article_number"] = article_match.group(1)

            chunks.append(
                Chunk(
                    content=content,
                    chunk_index=idx,
                    char_start=pos,
                    char_end=pos + len(content),
                    metadata=chunk_meta,
                )
            )
            pos += len(content)

        return chunks

    def _split_fixed(self, text: str) -> list[str]:
        """Cắt text dài thành các đoạn nhỏ với overlap."""
        parts: list[str] = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            parts.append(text[start:end])
            start = end - self.chunk_overlap
        return parts
