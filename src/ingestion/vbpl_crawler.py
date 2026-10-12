"""Crawler thu thập văn bản QPPL từ vbpl.vn.

VBPL (Văn bản pháp luật) là cổng thông tin chính thức của Chính phủ Việt Nam
cung cấp toàn bộ văn bản quy phạm pháp luật.

Lưu ý: Crawler tuân thủ robots.txt và rate limiting để không làm ảnh hưởng
đến hệ thống của cơ quan nhà nước.
"""

from __future__ import annotations

import logging
from typing import Any

from src.ingestion.base import BaseIngester, IngestionResult

logger = logging.getLogger(__name__)

# Các loại văn bản VBPL hỗ trợ
VBPL_DOC_TYPES = {
    "luat": "law",
    "nghi-dinh": "decree",
    "thong-tu": "circular",
    "quyet-dinh": "decision",
    "nghi-quyet": "resolution",
    "phap-lenh": "ordinance",
}


class VBPLCrawler(BaseIngester):
    """Thu thập văn bản QPPL từ vbpl.vn.

    Sử dụng:
        async with VBPLCrawler(base_url="https://vbpl.vn") as crawler:
            results = await crawler.ingest(doc_type="law", max_docs=100)
    """

    source_name = "vbpl"
    request_delay_sec = 1.5

    def __init__(self, base_url: str = "https://vbpl.vn", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = base_url.rstrip("/")

    async def fetch(self, url: str) -> str:
        """Tải HTML từ VBPL."""
        response = await self._get(url)
        return response.text

    async def parse(self, raw: str, url: str) -> dict[str, Any]:  # type: ignore[override]
        """Phân tích HTML VBPL thành dict chuẩn hoá.

        TODO: Implement sau khi phân tích cấu trúc HTML của vbpl.vn
        """
        raise NotImplementedError("VBPLCrawler.parse() — implement in Phase 2")

    async def ingest(  # type: ignore[override]
        self,
        doc_type: str = "law",
        max_docs: int = 50,
        db_session: Any = None,
    ) -> list[IngestionResult]:
        """Thu thập và lưu văn bản QPPL vào DB.

        Args:
            doc_type: Loại văn bản (law, decree, circular, ...)
            max_docs: Số tài liệu tối đa cần thu thập
            db_session: AsyncSession của SQLAlchemy

        Returns:
            Danh sách IngestionResult cho từng tài liệu đã xử lý
        """
        raise NotImplementedError("VBPLCrawler.ingest() — implement in Phase 2")

    def _build_list_url(self, doc_type: str, page: int = 1) -> str:
        """Xây dựng URL trang danh sách văn bản."""
        # TODO: Phân tích URL pattern của vbpl.vn
        return f"{self.base_url}/Pages/vbpq-tim-kiem.aspx?type={doc_type}&page={page}"
