"""Interface cơ sở cho tất cả document parser.

Định nghĩa:
- ParsedDocument: dataclass chứa kết quả parse
- BaseParser: ABC với method parse() phải được implement
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ParsedDocument:
    """Kết quả phân tích tài liệu đã chuẩn hoá.

    Attributes:
        title: Tiêu đề tài liệu (nếu phát hiện được)
        content: Toàn bộ nội dung text đã làm sạch
        sections: Các phần/mục được phân tách (nếu có cấu trúc)
        metadata: Thông tin bổ sung (số trang, tác giả, ngày, ...)
        source_path: Đường dẫn file nguồn
        parse_errors: Danh sách lỗi/cảnh báo trong quá trình parse
        page_count: Số trang
        parse_method: text_extraction | ocr | mixed
        warnings: Cảnh báo trong quá trình phân tích
    """

    title: str | None
    content: str
    sections: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: str | None = None
    parse_errors: list[str] = field(default_factory=list)
    page_count: int | None = None
    parse_method: str = "text_extraction"
    warnings: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """Trả về True nếu không có nội dung."""
        return not self.content or not self.content.strip()

    @property
    def word_count(self) -> int:
        """Ước tính số từ trong nội dung."""
        return len(self.content.split()) if self.content else 0


class BaseParser(ABC):
    """Lớp cơ sở trừu tượng cho tất cả document parser."""

    @abstractmethod
    def parse(self, source: Path | bytes | str) -> ParsedDocument:
        """Phân tích tài liệu và trả về ParsedDocument.

        Args:
            source: Đường dẫn file, bytes của file, hoặc string nội dung

        Returns:
            ParsedDocument với nội dung đã chuẩn hoá

        Raises:
            ValueError: Nếu tài liệu rỗng hoặc không đọc được
            NotImplementedError: Nếu format không được hỗ trợ
        """
        ...

    @abstractmethod
    def supports(self, source: Path | str) -> bool:
        """Kiểm tra parser này có hỗ trợ định dạng file không."""
        ...

    def _clean_text(self, text: str) -> str:
        """Làm sạch text: xoá ký tự thừa, chuẩn hoá khoảng trắng."""
        import re
        # Chuẩn hoá line ending
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Xoá khoảng trắng thừa cuối dòng
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        # Không để quá 2 dòng trắng liên tiếp
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
