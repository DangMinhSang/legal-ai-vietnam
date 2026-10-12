"""Precedent retriever — tìm kiếm án lệ tương tự."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.legal_rag.retriever import LegalRetriever, RetrievalResult


class PrecedentRetriever:
    """Truy vấn các án lệ có tình huống pháp lý tương tự."""

    def __init__(self, retriever: LegalRetriever | None = None) -> None:
        self.retriever = retriever or LegalRetriever()

    async def find_similar_precedents(
        self,
        case_facts: str,
        session: AsyncSession,
        top_k: int = 5,
        legal_domain: str | None = None,
        mode: str = "hybrid",
    ) -> list[RetrievalResult]:
        """Tìm án lệ tương tự với tình tiết vụ án."""
        results = await self.retriever.retrieve(
            case_facts,
            session=session,
            top_k=top_k,
            source_type="precedent",
            mode=mode,
        )
        # Chỉ giữ lại kết quả từ án lệ và đảm bảo nguồn gốc án lệ (provenance check)
        precedent_results = [r for r in results if r.precedent_id is not None]
        return precedent_results[:top_k]
