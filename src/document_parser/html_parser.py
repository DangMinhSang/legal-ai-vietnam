"""HTML parser cho nội dung pháp lý từ các cổng thông tin.

Dùng BeautifulSoup4 + lxml để:
- Xoá script, style, nav, footer, quảng cáo
- Trích xuất nội dung chính
- Giữ nguyên cấu trúc điều/khoản Việt Nam
- Chuẩn hoá khoảng trắng và encoding UTF-8
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from src.document_parser.base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)

# Tags cần xoá hoàn toàn (kể cả nội dung bên trong)
REMOVE_TAGS = {
    "script", "style", "nav", "footer", "header",
    "aside", "advertisement", "iframe", "noscript",
}

# Tags chỉ unwrap (giữ nội dung, xoá tag)
UNWRAP_TAGS = {"span", "div", "section", "article", "main"}


class HtmlParser(BaseParser):
    """Parser cho trang HTML từ VBPL và Toà án.

    Sử dụng:
        parser = HtmlParser()
        doc = parser.parse("<html>...</html>")
        print(doc.content[:500])
    """

    def supports(self, source: Path | str) -> bool:
        ext = str(source).lower()
        return ext.endswith((".html", ".htm"))

    def parse(self, source: Path | bytes | str) -> ParsedDocument:
        """Phân tích HTML và trích xuất văn bản pháp lý.

        Args:
            source: Path đến file HTML, bytes, hoặc string HTML

        Returns:
            ParsedDocument với nội dung text đã làm sạch
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise ImportError("beautifulsoup4 is required: pip install beautifulsoup4 lxml") from exc

        errors: list[str] = []
        metadata: dict[str, Any] = {}

        # Đọc HTML source
        if isinstance(source, Path):
            html_content = source.read_text(encoding="utf-8", errors="replace")
            metadata["source_path"] = str(source)
        elif isinstance(source, bytes):
            html_content = source.decode("utf-8", errors="replace")
        else:
            html_content = source

        if not html_content.strip():
            raise ValueError("HTML source is empty.")

        soup = BeautifulSoup(html_content, "lxml")

        # Lấy title từ <title> tag
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None
        metadata["html_title"] = title

        # Xoá các tags không cần thiết
        for tag in REMOVE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()

        # Lấy text từ toàn bộ body
        body = soup.find("body") or soup
        text = body.get_text(separator="\n", strip=False)

        if not text.strip():
            errors.append("No text content extracted from HTML.")
            return ParsedDocument(
                title=title,
                content="",
                metadata=metadata,
                parse_errors=errors,
            )

        text = self._clean_text(text)

        # Phân tách theo điều luật
        sections = self._split_by_article(text)

        return ParsedDocument(
            title=title,
            content=text,
            sections=sections,
            metadata=metadata,
            source_path=metadata.get("source_path"),
            parse_errors=errors,
        )

    def _split_by_article(self, text: str) -> list[dict[str, str]]:
        """Phân tách văn bản theo điều luật."""
        pattern = re.compile(
            r"(?:^|\n)((?:Điều|ĐIỀU)\s+\d+[a-z]?\.?\s+[^\n]+)",
            re.MULTILINE,
        )
        sections: list[dict[str, str]] = []
        matches = list(pattern.finditer(text))
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append({
                "header": match.group(1).strip(),
                "content": text[start:end].strip(),
            })
        return sections
