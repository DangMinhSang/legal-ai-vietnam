"""Case retriever — tìm kiếm bản án và vụ án tương tự."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.legal_rag.retriever import LegalRetriever, RetrievalResult


class CaseRetriever:
    """Truy vấn các bản án có tình tiết tương đồng."""

    def __init__(self, retriever: LegalRetriever | None = None) -> None:
        self.retriever = retriever or LegalRetriever()

    async def find_similar_cases(
        self,
        query: str,
        session: AsyncSession,
        top_k: int = 5,
        legal_domain: str | None = None,
        mode: str = "hybrid",
    ) -> list[RetrievalResult]:
        """Tìm các bản án tương tự dựa trên mô tả tình tiết."""
        results = await self.retriever.retrieve(
            query,
            session=session,
            top_k=top_k,
            source_type="judgment",
            mode=mode,
        )
        judgment_results = [r for r in results if r.judgment_document_id is not None]
        return judgment_results[:top_k]
