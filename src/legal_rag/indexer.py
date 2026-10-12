"""Legal indexer — tạo embedding và lưu vào sqlite-vec.

Dùng fastembed (ONNX runtime, không cần PyTorch hay GPU)
để tạo embedding cho các chunk văn bản pháp luật.
Lưu vào bảng text_chunks (ORM) và vec_text_chunks (sqlite-vec virtual table).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TextChunk
from src.legal_rag.chunker import Chunk

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIM = 768


class LegalIndexer:
    """Tạo embedding và lưu trữ vector cho văn bản pháp luật.

    Sử dụng:
        indexer = LegalIndexer()
        await indexer.index_chunks(chunks, doc_id="...", session=db)
    """

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        dim: int = EMBEDDING_DIM,
    ) -> None:
        self.model_name = model_name
        self.dim = dim
        self._embedder: Any = None

    def _get_embedder(self) -> Any:
        """Khởi tạo embedder (ưu tiên EmbeddingService singleton, fallback sang fastembed trực tiếp)."""
        if self._embedder is None:
            try:
                from src.services.embedding_service import EmbeddingService
                return EmbeddingService.get_instance(model_name=self.model_name)
            except Exception:
                try:
                    from fastembed import TextEmbedding
                    self._embedder = TextEmbedding(model_name=self.model_name)
                    logger.info("Loaded fastembed model: %s", self.model_name)
                except ImportError as exc:
                    raise ImportError("fastembed is required: pip install fastembed") from exc
        return self._embedder

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Tạo embedding cho danh sách văn bản dùng embedder."""
        embedder = self._get_embedder()
        if hasattr(embedder, "embed_texts"):
            return embedder.embed_texts(texts)
        embeddings = list(embedder.embed(texts))
        return [emb.tolist() if hasattr(emb, "tolist") else list(emb) for emb in embeddings]

    async def index_chunks(
        self,
        chunks: list[Chunk],
        legal_document_id: str | None = None,
        precedent_id: str | None = None,
        judgment_document_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> list[str]:
        """Tạo embedding và lưu chunks vào DB + sqlite-vec.

        Args:
            chunks: Danh sách Chunk từ LegalChunker
            legal_document_id: ID văn bản QPPL (nếu có)
            precedent_id: ID án lệ (nếu có)
            judgment_document_id: ID bản án (nếu có)
            session: AsyncSession của SQLAlchemy

        Returns:
            Danh sách ID của các TextChunk đã tạo
        """
        if not chunks:
            return []

        if session is None:
            raise ValueError("AsyncSession is required to index chunks.")

        # 1. Tạo embedding bằng fastembed
        texts = [c.content for c in chunks]
        embeddings = self.embed_texts(texts)

        # 2. Tạo ORM TextChunk records
        chunk_ids: list[str] = []
        orm_chunks: list[TextChunk] = []

        for chunk, emb in zip(chunks, embeddings):
            chunk_id = str(uuid.uuid4())
            orm_chunk = TextChunk(
                id=chunk_id,
                legal_document_id=legal_document_id,
                precedent_id=precedent_id,
                judgment_document_id=judgment_document_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                embedding_model=self.model_name,
                embedding=emb,
                embedding_dim=len(emb),
                meta=chunk.metadata,
            )
            orm_chunks.append(orm_chunk)
            chunk_ids.append(chunk_id)

        session.add_all(orm_chunks)
        await session.flush()

        # 3. Insert vào sqlite-vec virtual table
        import json
        for chunk_id, emb in zip(chunk_ids, embeddings):
            emb_json = json.dumps(emb)
            await session.execute(
                text("INSERT INTO vec_text_chunks(chunk_id, embedding) VALUES (:id, :emb)"),
                {"id": chunk_id, "emb": emb_json},
            )

        logger.info("Indexed %d chunks (doc_id=%s)", len(chunks), legal_document_id)
        return chunk_ids
