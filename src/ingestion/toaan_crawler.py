"""Crawler thu thập bản án từ congbobanan.toaan.gov.vn.

Cổng công bố bản án của Toà án nhân dân tối cao Việt Nam.
Bản án được công bố theo Nghị quyết 03/2017/NQ-HĐTP.
"""

from __future__ import annotations

import logging
from typing import Any

from src.ingestion.base import BaseIngester, IngestionResult

logger = logging.getLogger(__name__)

JUDGMENT_TYPES = {
    "HSST": "first_instance",   # Hình sự sơ thẩm
    "HSPT": "appeal",           # Hình sự phúc thẩm
    "HSGT": "cassation",        # Hình sự giám đốc thẩm
    "DSST": "first_instance",   # Dân sự sơ thẩm
    "DSPT": "appeal",           # Dân sự phúc thẩm
    "HCST": "first_instance",   # Hành chính sơ thẩm
}

LEGAL_DOMAINS = {
    "HS": "criminal",
    "DS": "civil",
    "HC": "administrative",
    "KD": "commercial",
    "LD": "labor",
    "HN": "family",
}


class ToanAnCrawler(BaseIngester):
    """Thu thập bản án từ congbobanan.toaan.gov.vn.

    Sử dụng:
        async with ToanAnCrawler() as crawler:
            results = await crawler.ingest(domain="criminal", year=2023)
    """

    source_name = "toaan"
    request_delay_sec = 2.0  # Rate limit cao hơn — server nhà nước

    def __init__(
        self,
        base_url: str = "https://congbobanan.toaan.gov.vn",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.base_url = base_url.rstrip("/")

    async def fetch(self, url: str) -> str:
        response = await self._get(url)
        return response.text

    async def parse(self, raw: str, url: str) -> dict[str, Any]:  # type: ignore[override]
        """Phân tích trang bản án thành dict chuẩn hoá.

        TODO: Implement sau khi phân tích cấu trúc HTML của toaan.gov.vn
        """
        raise NotImplementedError("ToanAnCrawler.parse() — implement in Phase 2")

    async def ingest(  # type: ignore[override]
        self,
        domain: str = "criminal",
        year: int | None = None,
        max_docs: int = 50,
        db_session: Any = None,
    ) -> list[IngestionResult]:
        """Thu thập và lưu bản án vào DB.

        Args:
            domain: Lĩnh vực pháp lý (criminal, civil, administrative, ...)
            year: Năm ban hành bản án (None = tất cả)
            max_docs: Số bản án tối đa
            db_session: AsyncSession của SQLAlchemy
        """
        raise NotImplementedError("ToanAnCrawler.ingest() — implement in Phase 2")

    @staticmethod
    def detect_domain(judgment_number: str) -> str:
        """Xác định lĩnh vực pháp lý từ số bản án.

        Ví dụ: "15/2023/HSST" → "criminal"
        """
        number_upper = judgment_number.upper()
        for code, domain in LEGAL_DOMAINS.items():
            if code in number_upper:
                return domain
        return "unknown"

    @staticmethod
    def detect_judgment_type(judgment_number: str) -> str:
        """Xác định loại bản án từ số bản án.

        Ví dụ: "15/2023/HSST" → "first_instance"
        """
        number_upper = judgment_number.upper()
        for code, jtype in JUDGMENT_TYPES.items():
            if code in number_upper:
                return jtype
        return "unknown"
