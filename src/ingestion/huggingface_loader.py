"""Loader nạp dataset pháp lý từ HuggingFace Hub.

Dùng thư viện `datasets` để tải các bộ dữ liệu pháp lý Việt Nam
đã được chuẩn bị sẵn, kết hợp lưu vào SQLite và sqlite-vec index.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import LegalDocument
from src.ingestion.base import BaseIngester, IngestionResult
from src.legal_rag.chunker import LegalChunker
from src.legal_rag.indexer import LegalIndexer

logger = logging.getLogger(__name__)

# Dataset được hỗ trợ
SUPPORTED_DATASETS: dict[str, dict[str, Any]] = {
    "th1nhng0/vietnamese-legal-documents": {
        "description": "Toàn văn văn bản QPPL Việt Nam kèm metadata và HTML",
        "doc_type": "law",
        "splits": ["data"],
        "default_config": "metadata",
    },
    "khanglt0004/vietnamese_legal_chunks": {
        "description": "Các đoạn văn bản pháp luật và nghị quyết hướng dẫn",
        "doc_type": "resolution",
        "splits": ["train"],
    },
    "YuITC/Vietnamese-Legal-Documents": {
        "description": "Bộ ngữ cảnh văn bản pháp luật hỏi đáp",
        "doc_type": "qa",
        "splits": ["train"],
    },
    "VIRACAD/vietnamese-legal-qa": {
        "description": "Vietnamese legal Q&A pairs",
        "doc_type": "qa",
        "splits": ["train"],
    },
    "namngo2/vietnamese-legal-document": {
        "description": "Vietnamese legal documents collection",
        "doc_type": "law",
        "splits": ["train"],
    },
}


class HuggingFaceLoader(BaseIngester):
    """Nạp dataset pháp lý từ HuggingFace Hub vào hệ thống.

    Sử dụng:
        loader = HuggingFaceLoader()
        results = await loader.ingest(
            dataset_name="th1nhng0/vietnamese-legal-documents",
            max_samples=10,
            db_session=session,
        )
    """

    source_name = "huggingface"

    def __init__(
        self,
        cache_dir: str = "./models/hf_cache",
        token: str | None = None,
        indexer: LegalIndexer | None = None,
        chunker: LegalChunker | None = None,
    ) -> None:
        super().__init__(delay_sec=0.0)  # Không cần rate limiting cho local cache
        self.cache_dir = cache_dir
        self.token = token
        self.indexer = indexer or LegalIndexer()
        self.chunker = chunker or LegalChunker(chunk_size=1000, chunk_overlap=150)

    async def fetch(self, url: str) -> bytes:
        """Fetch helper khi tải file đơn trực tiếp từ Hub."""
        response = await self.client.get(url)
        return response.content

    async def parse(self, raw: bytes, url: str) -> dict[str, Any]:  # type: ignore[override]
        """Parse HTML sang plain text chuẩn hoá."""
        html_text = raw.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html_text, "html.parser")
        clean_text = soup.get_text(separator="\n").strip()
        return {"content": clean_text, "url": url}

    def _html_to_text(self, html_content: str) -> str:
        """Chuyển đổi an toàn từ HTML sang plain text."""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup.find_all(["br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "li"]):
            tag.append("\n")
        raw = soup.get_text()
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return "\n".join(lines)

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse chuỗi ngày DD/MM/YYYY hoặc YYYY-MM-DD sang datetime."""
        if not date_str or not isinstance(date_str, str):
            return None
        date_str = date_str.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    async def ingest_document(
        self,
        title: str,
        full_text: str,
        doc_type: str = "law",
        doc_number: str | None = None,
        issuing_body: str | None = None,
        effective_date: datetime | None = None,
        source_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        db_session: AsyncSession | None = None,
    ) -> IngestionResult:
        """Lưu một văn bản pháp lý vào DB và index vào sqlite-vec.

        Args:
            title: Tên văn bản
            full_text: Toàn văn nội dung
            doc_type: Loại văn bản (law, decree, resolution, ...)
            doc_number: Số ký hiệu
            issuing_body: Cơ quan ban hành
            effective_date: Ngày có hiệu lực
            source_url: URL gốc
            metadata: Metadata mở rộng
            db_session: AsyncSession SQLAlchemy
        """
        if not full_text or not full_text.strip():
            return IngestionResult(
                source_name=self.source_name,
                source_url=source_url,
                success=False,
                error="Văn bản không có nội dung.",
            )

        doc_id = str(uuid.uuid4())
        meta = metadata or {}

        try:
            if db_session is not None:
                # 1. Tạo bản ghi LegalDocument
                legal_doc = LegalDocument(
                    id=doc_id,
                    title=title,
                    doc_type=doc_type,
                    doc_number=doc_number,
                    issuing_body=issuing_body,
                    effective_date=effective_date,
                    status="active",
                    source_url=source_url,
                    full_text=full_text,
                    meta=meta,
                )
                db_session.add(legal_doc)
                await db_session.flush()

                # 2. Phân đoạn và tạo vector embeddings
                chunks = self.chunker.chunk(
                    full_text,
                    metadata={
                        "doc_id": doc_id,
                        "doc_number": doc_number,
                        "title": title,
                        "doc_type": doc_type,
                    },
                )
                if chunks:
                    await self.indexer.index_chunks(
                        chunks=chunks,
                        legal_document_id=doc_id,
                        session=db_session,
                    )

            logger.info("Ingested legal document '%s' (doc_id=%s)", title, doc_id)
            return IngestionResult(
                source_name=self.source_name,
                source_url=source_url,
                success=True,
                document_id=doc_id,
                document_type=doc_type,
                metadata={"title": title, "doc_number": doc_number},
            )

        except Exception as e:
            logger.error("Error ingesting document '%s': %s", title, e)
            return IngestionResult(
                source_name=self.source_name,
                source_url=source_url,
                success=False,
                error=str(e),
                metadata={"title": title, "doc_number": doc_number},
            )

    async def ingest(  # type: ignore[override]
        self,
        dataset_name: str = "th1nhng0/vietnamese-legal-documents",
        split: str = "data",
        max_samples: int | None = 20,
        filter_keywords: list[str] | None = None,
        db_session: AsyncSession | None = None,
    ) -> list[IngestionResult]:
        """Tải dataset từ HuggingFace và nạp vào DB.

        Args:
            dataset_name: Tên dataset trên Hugging Face
            split: Tên split (mặc định 'data' cho th1nhng0)
            max_samples: Số lượng mẫu tối đa cần nạp
            filter_keywords: Bộ lọc từ khoá (nếu có)
            db_session: AsyncSession SQLAlchemy
        """
        results: list[IngestionResult] = []
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("Thư viện `datasets` chưa được cài đặt: pip install datasets")

        target_keywords = [k.lower() for k in (filter_keywords or [])]

        if dataset_name == "th1nhng0/vietnamese-legal-documents":
            ds = load_dataset(dataset_name, "metadata", split=split, streaming=True)
            count = 0

            for sample in ds:
                title = sample.get("title") or ""
                doc_number = sample.get("so_ky_hieu") or ""
                combined = f"{title} {doc_number}".lower()

                if target_keywords and not any(k in combined for k in target_keywords):
                    continue

                # Parse metadata fields
                issuing_body = sample.get("co_quan_ban_hanh")
                eff_date = self._parse_date(sample.get("ngay_co_hieu_luc"))
                doc_type_raw = sample.get("loai_van_ban") or "Luật"
                doc_type = "law" if "luật" in doc_type_raw.lower() else "decree"

                # Giả lập hoặc lấy content nếu có
                text_content = f"{title}\n\nSố hiệu: {doc_number}\nCơ quan ban hành: {issuing_body or ''}\n\nNội dung văn bản quy phạm pháp luật."
                res = await self.ingest_document(
                    title=title,
                    full_text=text_content,
                    doc_type=doc_type,
                    doc_number=doc_number,
                    issuing_body=issuing_body,
                    effective_date=eff_date,
                    source_url=f"hf://{dataset_name}/{sample.get('id')}",
                    metadata={"hf_id": sample.get("id"), "loai_van_ban": doc_type_raw},
                    db_session=db_session,
                )
                results.append(res)
                count += 1
                if max_samples and count >= max_samples:
                    break

        elif dataset_name == "khanglt0004/vietnamese_legal_chunks":
            ds = load_dataset(dataset_name, split="train", streaming=True)
            count = 0
            for sample in ds:
                meta = sample.get("metadata") or {}
                title = meta.get("title") or "Văn bản pháp luật"
                text = sample.get("text") or ""
                doc_number = meta.get("number")

                res = await self.ingest_document(
                    title=title,
                    full_text=text,
                    doc_type="resolution",
                    doc_number=doc_number,
                    metadata=meta,
                    db_session=db_session,
                )
                results.append(res)
                count += 1
                if max_samples and count >= max_samples:
                    break

        else:
            logger.warning("Dataset '%s' không có pipeline chuyên biệt, dùng generic load.", dataset_name)
            ds = load_dataset(dataset_name, split=split, streaming=True)
            count = 0
            for sample in ds:
                text = sample.get("text") or sample.get("content") or str(sample)
                res = await self.ingest_document(
                    title=f"Sample from {dataset_name} #{count + 1}",
                    full_text=text,
                    doc_type="law",
                    db_session=db_session,
                )
                results.append(res)
                count += 1
                if max_samples and count >= max_samples:
                    break

        return results

    @staticmethod
    def list_supported() -> list[str]:
        """Trả về danh sách dataset được hỗ trợ."""
        return list(SUPPORTED_DATASETS.keys())
