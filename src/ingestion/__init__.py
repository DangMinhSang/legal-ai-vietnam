"""Sub-package ingestion: thu thập dữ liệu pháp lý từ các nguồn bên ngoài.

Các module:
- base: lớp cơ sở BaseIngester với retry logic và rate limiting
- vbpl_crawler: thu thập văn bản QPPL từ vbpl.vn
- toaan_crawler: thu thập bản án từ congbobanan.toaan.gov.vn
- huggingface_loader: nạp dataset pháp lý từ HuggingFace Hub
"""

from src.ingestion.base import BaseIngester

__all__ = ["BaseIngester"]
