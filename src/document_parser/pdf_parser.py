"""PDF parser dùng pypdf với OCR fallback qua rapidocr.

Chiến lược:
1. Thử trích xuất text layer dùng pypdf (nhanh, chính xác)
2. Nếu ít hơn MIN_TEXT_CHARS ký tự → tài liệu là scan → dùng rapidocr
3. Làm sạch text và phát hiện cấu trúc điều/khoản Việt Nam
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from src.document_parser.base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)

# Nếu trích xuất được ít hơn số ký tự này → coi là scan PDF
MIN_TEXT_CHARS = 100

# Pattern phát hiện điều trong văn bản pháp luật Việt Nam
ARTICLE_PATTERN = re.compile(
    r"(?:^|\n)(Điều\s+\d+[a-z]?\.?\s+[^\n]+)",
    re.MULTILINE,
)


class PdfParser(BaseParser):
    """Parser cho file PDF pháp lý Việt Nam.

    Sử dụng:
        parser = PdfParser(ocr_fallback=True)
        doc = parser.parse(Path("luat_kd_bh.pdf"))
        print(doc.content[:500])
    """

    def __init__(self, ocr_fallback: bool = False) -> None:
        """
        Args:
            ocr_fallback: Có dùng rapidocr khi không có text layer không.
                          Mặc định False để tránh phụ thuộc vào rapidocr.
        """
        self.ocr_fallback = ocr_fallback

    def supports(self, source: Path | str) -> bool:
        return str(source).lower().endswith(".pdf")

    def parse(self, source: Path | bytes | str) -> ParsedDocument:
        """Phân tích file PDF.

        Args:
            source: Path đến file PDF hoặc bytes của PDF

        Returns:
            ParsedDocument với nội dung text

        Raises:
            ValueError: Nếu file rỗng hoặc không đọc được
        """
        try:
            import pypdf
        except ImportError as exc:
            raise ImportError("pypdf is required: pip install pypdf") from exc

        errors: list[str] = []
        metadata: dict[str, Any] = {}

        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise ValueError(f"PDF file not found: {path}")
            reader = pypdf.PdfReader(str(path))
            metadata["source_path"] = str(path)
        else:
            import io
            reader = pypdf.PdfReader(io.BytesIO(source))

        metadata["page_count"] = len(reader.pages)

        # Thử trích xuất PDF metadata
        if reader.metadata:
            raw_meta = reader.metadata
            if raw_meta.get("/Title"):
                metadata["pdf_title"] = raw_meta["/Title"]
            if raw_meta.get("/Author"):
                metadata["pdf_author"] = raw_meta["/Author"]

        # Trích xuất text từ tất cả trang
        pages_text: list[str] = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                pages_text.append(text)
            except Exception as exc:
                errors.append(f"Page {i + 1} extract error: {exc}")
                pages_text.append("")

        full_text = "\n\n".join(pages_text)

        # OCR fallback nếu không có text layer
        if len(full_text.strip()) < MIN_TEXT_CHARS and self.ocr_fallback:
            logger.warning("PDF appears to be scanned. Attempting OCR fallback.")
            full_text = self._ocr_fallback(source, errors)

        if not full_text.strip():
            raise ValueError("PDF contains no extractable text.")

        full_text = self._clean_text(full_text)

        # Phát hiện tiêu đề từ dòng đầu tiên
        title = self._detect_title(full_text, metadata)

        # Phân tách theo điều (sections)
        sections = self._split_by_article(full_text)

        return ParsedDocument(
            title=title,
            content=full_text,
            sections=sections,
            metadata=metadata,
            source_path=metadata.get("source_path"),
            parse_errors=errors,
        )

    def _detect_title(self, text: str, metadata: dict[str, Any]) -> str | None:
        """Lấy tiêu đề từ PDF metadata hoặc dòng đầu tiên."""
        if metadata.get("pdf_title"):
            return str(metadata["pdf_title"])
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            return lines[0][:200]  # Giới hạn 200 ký tự
        return None

    def _split_by_article(self, text: str) -> list[dict[str, str]]:
        """Phân tách văn bản theo điều luật."""
        sections: list[dict[str, str]] = []
        matches = list(ARTICLE_PATTERN.finditer(text))
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()
            sections.append({
                "header": match.group(1).strip(),
                "content": section_text,
            })
        return sections

    def _ocr_fallback(self, source: Path | bytes | str, errors: list[str]) -> str:
        """OCR fallback dùng rapidocr-onnxruntime.

        TODO: Implement trong Phase 2 khi cần xử lý PDF scan.
        """
        errors.append("OCR fallback not yet implemented — returning empty string.")
        logger.error("OCR fallback requested but not implemented.")
        return ""
