"""Lớp cơ sở cho tất cả data ingester.

Cung cấp:
- Rate limiting giữa các request
- Retry logic với exponential backoff (dùng tenacity)
- Logging chuẩn hoá với loguru
- Interface chung: fetch() và ingest()
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Kết quả của một lần thu thập tài liệu."""

    source_name: str
    source_url: str | None
    success: bool
    document_id: str | None = None
    document_type: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.utcnow)


class BaseIngester(ABC):
    """Lớp cơ sở trừu tượng cho tất cả data ingester.

    Subclass phải implement:
    - source_name: tên nguồn dữ liệu (vbpl, toaan, huggingface, ...)
    - fetch(url): tải nội dung thô từ URL
    - parse(raw): chuyển đổi nội dung thô thành dict chuẩn hoá
    - ingest(target): pipeline đầy đủ fetch → parse → lưu DB
    """

    source_name: str = "base"
    request_delay_sec: float = 1.5
    max_retries: int = 3
    timeout_sec: float = 30.0

    def __init__(self, delay_sec: float | None = None) -> None:
        if delay_sec is not None:
            self.request_delay_sec = delay_sec
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BaseIngester":
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_sec),
            headers={"User-Agent": "LegalAIResearch/0.1 (academic; contact: research@example.com)"},
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Ingester must be used as async context manager.")
        return self._client

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _get(self, url: str, **kwargs: Any) -> httpx.Response:
        """GET request với retry và rate limiting."""
        await asyncio.sleep(self.request_delay_sec)
        response = await self.client.get(url, **kwargs)
        response.raise_for_status()
        return response

    @abstractmethod
    async def fetch(self, url: str) -> bytes | str:
        """Tải nội dung thô từ URL."""
        ...

    @abstractmethod
    async def parse(self, raw: bytes | str, url: str) -> dict[str, Any]:
        """Chuyển đổi nội dung thô thành dict chuẩn hoá."""
        ...

    @abstractmethod
    async def ingest(self, **kwargs: Any) -> list[IngestionResult]:
        """Pipeline đầy đủ: fetch → parse → lưu vào DB."""
        ...

    def _log_result(self, result: IngestionResult) -> None:
        if result.success:
            logger.info(
                "[%s] Ingested %s → doc_id=%s",
                self.source_name,
                result.source_url,
                result.document_id,
            )
        else:
            logger.error(
                "[%s] Failed %s: %s",
                self.source_name,
                result.source_url,
                result.error,
            )
