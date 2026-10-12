"""Case indexer — index hồ sơ vụ án và bản án vào sqlite-vec."""

from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import JudgmentDocument
from src.legal_rag.chunker import LegalChunker
from src.legal_rag.indexer import LegalIndexer

logger = logging.getLogger(__name__)


class CaseIndexer:
    """Index bản án và vụ án vào vector store."""

    def __init__(self, indexer: LegalIndexer | None = None) -> None:
        self.indexer = indexer or LegalIndexer()
        self.chunker = LegalChunker(chunk_size=1000, chunk_overlap=150)

    async def index_judgment(self, judgment: JudgmentDocument, session: AsyncSession) -> list[str]:
        """Index một bản án vào sqlite-vec."""
        text = judgment.full_text or ""
        if not text:
            return []
        chunks = self.chunker.chunk(
            text,
            metadata={
                "judgment_number": judgment.judgment_number,
                "judgment_type": judgment.judgment_type,
                "legal_domain": judgment.legal_domain,
            },
        )
        return await self.indexer.index_chunks(
            chunks, judgment_document_id=judgment.id, session=session
        )
