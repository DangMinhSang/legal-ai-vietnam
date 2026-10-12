"""Sub-package document_parser: phân tích và trích xuất nội dung tài liệu.

Hỗ trợ các định dạng:
- PDF: dùng pypdf (ưu tiên) với fallback sang rapidocr cho ảnh scan
- HTML: dùng BeautifulSoup4 + lxml để làm sạch HTML từ crawler
- DOCX: dùng python-docx cho văn bản Word

Các module:
- base: lớp cơ sở BaseParser định nghĩa interface chung
- pdf_parser: phân tích file PDF (text layer + OCR fallback)
- html_parser: phân tích HTML thành văn bản thuần
"""

from src.document_parser.base import BaseParser, ParsedDocument
from src.document_parser.parser import DocumentParser

__all__ = ["BaseParser", "ParsedDocument", "DocumentParser"]
