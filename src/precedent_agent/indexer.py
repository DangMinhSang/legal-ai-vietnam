"""Precedent indexer — đánh chỉ mục án lệ vào sqlite-vec."""

from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Precedent
from src.legal_rag.chunker import Chunk, LegalChunker
from src.legal_rag.indexer import LegalIndexer

logger = logging.getLogger(__name__)


class PrecedentIndexer:
    """Index án lệ vào sqlite-vec để phục vụ tìm kiếm ngữ nghĩa."""

    def __init__(self, indexer: LegalIndexer | None = None) -> None:
        self.indexer = indexer or LegalIndexer()
        self.chunker = LegalChunker(chunk_size=800, chunk_overlap=100)

    async def index_precedent(self, precedent: Precedent, session: AsyncSession) -> list[str]:
        """Tạo embedding và index một án lệ."""
        text = f"{precedent.title}\n\n{precedent.legal_issue_summary or ''}\n\n{precedent.legal_solution or ''}"
        chunks = self.chunker.chunk(text, metadata={"precedent_number": precedent.precedent_number})
        return await self.indexer.index_chunks(chunks, precedent_id=precedent.id, session=session)
