"""Integration tests cho RAG pipeline đầy đủ.

Kiểm tra toàn bộ luồng:
1. Chunking tài liệu pháp lý
2. Tạo embedding và index vào sqlite-vec
3. Retrieval theo vector similarity
4. Kiểm tra metadata và kết quả rỗng
5. Precedent retrieval

Sử dụng session in-memory SQLite fixture và mock embedder (768 chiều)
để test nhanh và không cần tải trước model 1GB.
"""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock

from src.legal_rag.chunker import Chunk, LegalChunker
from src.legal_rag.indexer import LegalIndexer
from src.legal_rag.retriever import LegalRetriever
from src.precedent_agent.retriever import PrecedentRetriever
from src.db.models import LegalDocument, Precedent


class DeterministicMockEmbedder:
    """Mock embedder tạo vector 768 chiều từ hash của text để kiểm tra tương đồng."""

    def __init__(self, dim: int = 768):
        self.dim = dim

    def embed(self, texts: list[str]):
        results = []
        for text in texts:
            # Deterministic pseudo-random vector based on text hash
            seed = abs(hash(text)) % (2**31)
            rng = np.random.default_rng(seed)
            vec = rng.standard_normal(self.dim).astype(np.float32)
            # Normalize to unit length for cosine distance
            vec /= np.linalg.norm(vec) + 1e-9
            results.append(vec)
        return results


@pytest.fixture
def mock_embedder():
    return DeterministicMockEmbedder(dim=768)


@pytest.fixture
def mock_indexer(mock_embedder):
    indexer = LegalIndexer(dim=768)
    indexer._embedder = mock_embedder
    return indexer


@pytest.fixture
def mock_retriever(mock_embedder):
    retriever = LegalRetriever(top_k=5)
    retriever._embedder = mock_embedder
    return retriever


class TestRagPipelineIntegration:
    """End-to-end RAG pipeline với SQLite + sqlite-vec thật."""

    @pytest.mark.asyncio
    async def test_empty_index_returns_empty_results(self, db_session, mock_retriever):
        """Retrieval trên index rỗng phải trả về list rỗng, không raise exception."""
        results = await mock_retriever.retrieve(
            query="hành vi trộm cắp tài sản",
            session=db_session,
            top_k=5,
        )
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_index_and_retrieve_legal_document(
        self, db_session, mock_indexer, mock_retriever
    ):
        """Index chunk và truy vấn lại bằng chính nội dung chunk đó."""
        # 1. Tạo LegalDocument
        doc = LegalDocument(
            title="Bộ luật Hình sự 2015",
            doc_type="law",
            doc_number="100/2015/QH13",
            status="active",
        )
        db_session.add(doc)
        await db_session.flush()

        # 2. Tạo chunks
        content_168 = "Điều 168. Tội cướp tài sản. Người nào dùng vũ lực chiếm đoạt tài sản thì bị phạt tù từ 03 đến 10 năm."
        content_173 = "Điều 173. Tội trộm cắp tài sản. Người nào lén lút chiếm đoạt tài sản của người khác trị giá từ 2 triệu đồng."
        chunks = [
            Chunk(
                content=content_168,
                chunk_index=0,
                char_start=0,
                char_end=len(content_168),
                metadata={"article": "168"},
            ),
            Chunk(
                content=content_173,
                chunk_index=1,
                char_start=0,
                char_end=len(content_173),
                metadata={"article": "173"},
            ),
        ]

        # 3. Index chunks
        chunk_ids = await mock_indexer.index_chunks(
            chunks=chunks,
            legal_document_id=doc.id,
            session=db_session,
        )
        assert len(chunk_ids) == 2

        # 4. Truy vấn chính xác nội dung Điều 168
        query = "Điều 168. Tội cướp tài sản. Người nào dùng vũ lực chiếm đoạt tài sản thì bị phạt tù từ 03 đến 10 năm."
        results = await mock_retriever.retrieve(
            query=query,
            session=db_session,
            top_k=2,
        )

        assert len(results) >= 1
        # Top 1 kết quả phải là Điều 168
        top_result = results[0]
        assert "Điều 168" in top_result.content
        assert top_result.legal_document_id == doc.id

    @pytest.mark.asyncio
    async def test_chunk_metadata_preserved(
        self, db_session, mock_indexer
    ):
        """TextChunk lưu trong DB phải giữ đúng legal_document_id và metadata."""
        doc = LegalDocument(
            title="Luật thử nghiệm",
            doc_type="law",
            doc_number="TEST/2023",
            status="active",
        )
        db_session.add(doc)
        await db_session.flush()

        content_test = "Nội dung điều luật thử nghiệm về trách nhiệm bồi thường thiệt hại."
        chunks = [
            Chunk(
                content=content_test,
                chunk_index=0,
                char_start=0,
                char_end=len(content_test),
                metadata={"source_chapter": "Chương XX", "article": "584"},
            ),
        ]

        chunk_ids = await mock_indexer.index_chunks(
            chunks=chunks,
            legal_document_id=doc.id,
            session=db_session,
        )
        assert len(chunk_ids) == 1

        # Query trực tiếp từ DB để kiểm tra
        from sqlalchemy import select
        from src.db.models import TextChunk

        stmt = select(TextChunk).where(TextChunk.id == chunk_ids[0])
        result = await db_session.execute(stmt)
        orm_chunk = result.scalar_one_or_none()

        assert orm_chunk is not None
        assert orm_chunk.legal_document_id == doc.id
        assert orm_chunk.chunk_index == 0
        assert orm_chunk.meta.get("article") == "584"

    @pytest.mark.asyncio
    async def test_precedent_retrieval(
        self, db_session, mock_indexer, mock_retriever
    ):
        """Án lệ đã index phải được PrecedentRetriever tìm thấy."""
        precedent = Precedent(
            precedent_number="Án lệ số 01/2016/AL",
            title="Về vụ án Giết người",
            legal_issue_summary="Xác định tình tiết định khung hành vi có tính chất côn đồ",
        )
        db_session.add(precedent)
        await db_session.flush()

        content_prec = "Tình huống án lệ: Dùng hung khí nguy hiểm tấn công vô cớ vào vùng trọng yếu của nạn nhân."
        chunks = [
            Chunk(
                content=content_prec,
                chunk_index=0,
                char_start=0,
                char_end=len(content_prec),
                metadata={"type": "precedent"},
            )
        ]

        await mock_indexer.index_chunks(
            chunks=chunks,
            precedent_id=precedent.id,
            session=db_session,
        )

        precedent_retriever = PrecedentRetriever(retriever=mock_retriever)
        query = "Tình huống án lệ: Dùng hung khí nguy hiểm tấn công vô cớ vào vùng trọng yếu của nạn nhân."
        results = await precedent_retriever.find_similar_precedents(
            case_facts=query,
            session=db_session,
            top_k=3,
        )

        assert len(results) >= 1
        assert results[0].precedent_id == precedent.id
