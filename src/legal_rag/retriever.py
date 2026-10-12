"""Legal retriever — truy vấn văn bản pháp luật liên quan.

Hỗ trợ:
- Dense retrieval dùng sqlite-vec (cosine/L2 distance)
- BM25 keyword retrieval (tuỳ chọn)
- Hybrid search kết hợp cả hai
- Lọc theo loại văn bản và trạng thái hiệu lực
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Kết quả trả về từ retriever."""

    chunk_id: str
    content: str
    score: float                         # Điểm relevance (cao hơn = liên quan hơn)
    legal_document_id: str | None = None
    precedent_id: str | None = None
    judgment_document_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    cosine_similarity: float = 0.0       # Điểm tương đồng cosine [0.0, 1.0]


class LegalRetriever:
    """Truy vấn văn bản pháp luật dùng sqlite-vec.

    Sử dụng:
        retriever = LegalRetriever()
        results = await retriever.retrieve("quy định về bảo hiểm cháy nổ", session=db, top_k=5)
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        top_k: int = 10,
    ) -> None:
        self.embedding_model = embedding_model
        self.top_k = top_k
        self._embedder: Any = None

    def _get_embedder(self) -> Any:
        if self._embedder is None:
            try:
                from src.services.embedding_service import EmbeddingService
                return EmbeddingService.get_instance(model_name=self.embedding_model)
            except Exception:
                try:
                    from fastembed import TextEmbedding
                    self._embedder = TextEmbedding(model_name=self.embedding_model)
                except ImportError as exc:
                    raise ImportError("fastembed is required") from exc
        return self._embedder

    def embed_query(self, query: str) -> list[float]:
        """Tạo embedding cho câu truy vấn."""
        embedder = self._get_embedder()
        if hasattr(embedder, "embed_single"):
            return embedder.embed_single(query)
        if hasattr(embedder, "embed_texts"):
            return embedder.embed_texts([query])[0]
        embs = list(embedder.embed([query]))
        return embs[0].tolist() if hasattr(embs[0], "tolist") else list(embs[0])

    @staticmethod
    def _build_fts_query(text_query: str) -> str:
        """Xây dựng câu truy vấn FTS5 từ văn bản tìm kiếm có n-gram/phrase boosting."""
        clean = re.sub(r"[^\w\s]", " ", text_query)
        words = clean.split()
        stop_words = {
            "hành", "vi", "và", "hoặc", "của", "cho", "về", "trong", "do", "bị", "các",
            "những", "để", "có", "thì", "là", "được", "theo", "tại", "với", "người", "khác",
        }
        meaningful = [w for w in words if w.lower() not in stop_words and len(w) > 1]

        key_legal_phrases = [
            "cướp giật tài sản", "vận chuyển trái phép", "chất ma túy", "tham gia giao thông",
            "tham gia giao thông đường bộ", "giao thông đường bộ", "an toàn giao thông đường bộ",
            "vi phạm quy định về tham gia giao thông", "cướp tài sản", "trộm cắp tài sản",
            "lừa đảo chiếm đoạt tài sản", "chiếm đoạt tài sản", "cố ý gây thương tích",
            "tổn hại cho sức khỏe", "vùng trọng yếu", "giết người", "bị kích động mạnh",
            "vô ý làm chết người", "thủ đoạn gian dối", "đồng phạm", "có tính chất côn đồ",
            "dùng dao", "hung khí nguy hiểm", "dùng vũ lực ngay tức khắc", "gây chết người",
            "nồng độ cồn", "qua biên giới", "tài sản",
        ]
        lower_text = text_query.lower()
        phrases = [f'"{p}"' for p in key_legal_phrases if p in lower_text]

        parts = list(phrases)
        parts.extend(meaningful[:12])
        return " OR ".join(parts) if parts else text_query

    async def retrieve(
        self,
        query: str,
        session: AsyncSession,
        top_k: int | None = None,
        doc_type_filter: str | None = None,
        source_type: str | None = None,
        mode: str = "hybrid",
    ) -> list[RetrievalResult]:
        """Truy vấn các chunk liên quan nhất đến query.

        Args:
            query: Câu hỏi hoặc từ khoá tìm kiếm
            session: AsyncSession của SQLAlchemy
            top_k: Số kết quả trả về (mặc định lấy từ self.top_k)
            doc_type_filter: Lọc theo loại văn bản (law, decree, ...)
            source_type: Lọc nguồn gốc ('legal_doc', 'precedent', 'judgment', hoặc None)
            mode: Chế độ truy xuất ('hybrid', 'dense', 'bm25')

        Returns:
            Danh sách RetrievalResult đã sắp xếp theo điểm giảm dần
        """
        k = top_k or self.top_k
        query_emb = self.embed_query(query)
        query_emb_json = json.dumps(query_emb)

        # Xây dựng điều kiện lọc nguồn gốc (Provenance & Isolation)
        filter_conditions: list[str] = []
        filter_params: dict[str, Any] = {}

        if source_type == "legal_doc":
            filter_conditions.append("tc.legal_document_id IS NOT NULL AND tc.precedent_id IS NULL")
        elif source_type == "precedent":
            filter_conditions.append("tc.precedent_id IS NOT NULL")
        elif source_type == "judgment":
            filter_conditions.append("tc.judgment_document_id IS NOT NULL")

        if doc_type_filter:
            filter_conditions.append("json_extract(tc.meta, '$.doc_type') = :doc_type_filter")
            filter_params["doc_type_filter"] = doc_type_filter

        filter_clause = ""
        if filter_conditions:
            filter_clause = " AND " + " AND ".join(filter_conditions)

        # -------------------------------------------------------------------
        # 1. Dense retrieval qua sqlite-vec
        # -------------------------------------------------------------------
        dense_results: list[tuple[str, float, str, str | None, str | None, str | None, Any]] = []
        if mode in ("dense", "hybrid"):
            # Candidate pool rộng để SQLite lọc hậu kỳ chính xác
            k_vec = max(k * 20, 150) if filter_clause else k
            dense_sql = f"""
                SELECT
                    v.chunk_id,
                    v.distance,
                    tc.content,
                    tc.legal_document_id,
                    tc.precedent_id,
                    tc.judgment_document_id,
                    tc.meta
                FROM vec_text_chunks v
                JOIN text_chunks tc ON tc.id = v.chunk_id
                WHERE v.embedding MATCH :query_emb
                  AND k = :k_vec
                  {filter_clause}
                ORDER BY v.distance ASC
            """
            params = {"query_emb": query_emb_json, "k_vec": k_vec, **filter_params}
            try:
                rows = (await session.execute(text(dense_sql), params)).fetchall()
                dense_results = rows
            except Exception as e:
                logger.warning("Dense retrieval error: %s", e)
                dense_results = []

        # -------------------------------------------------------------------
        # 2. BM25 keyword retrieval qua fts_text_chunks (FTS5)
        # -------------------------------------------------------------------
        bm25_results: list[tuple[str, float, str, str | None, str | None, str | None, Any]] = []
        if mode in ("bm25", "hybrid"):
            fts_query = self._build_fts_query(query)
            if fts_query:
                bm25_sql = f"""
                    SELECT
                        fts.chunk_id,
                        bm25(fts_text_chunks) AS rank,
                        tc.content,
                        tc.legal_document_id,
                        tc.precedent_id,
                        tc.judgment_document_id,
                        tc.meta
                    FROM fts_text_chunks fts
                    JOIN text_chunks tc ON tc.id = fts.chunk_id
                    WHERE fts_text_chunks MATCH :fts_query
                      {filter_clause}
                    ORDER BY rank ASC
                    LIMIT :limit_bm25
                """
                params = {"fts_query": fts_query, "limit_bm25": max(k * 10, 50), **filter_params}
                try:
                    rows = (await session.execute(text(bm25_sql), params)).fetchall()
                    bm25_results = rows
                except Exception as e:
                    logger.debug("BM25 retrieval skipped or unavailable: %s", e)
                    bm25_results = []

        # -------------------------------------------------------------------
        # 3. Kết hợp kết quả (RRF hoặc fallback)
        # -------------------------------------------------------------------
        if mode == "dense" or (mode == "hybrid" and not bm25_results):
            results: list[RetrievalResult] = []
            for row in dense_results[:k]:
                chunk_id, distance, content, doc_id, prec_id, judg_id, meta = row
                dist_f = float(distance)
                score = 1.0 / (1.0 + dist_f)
                cos_sim = max(0.0, min(1.0, 1.0 - (dist_f**2) / 2.0))
                meta_dict = json.loads(meta) if isinstance(meta, str) else (meta or {})
                results.append(
                    RetrievalResult(
                        chunk_id=chunk_id,
                        content=content,
                        score=score,
                        legal_document_id=doc_id,
                        precedent_id=prec_id,
                        judgment_document_id=judg_id,
                        metadata=meta_dict,
                        cosine_similarity=cos_sim,
                    )
                )
            return results

        if mode == "bm25" or (mode == "hybrid" and not dense_results):
            results: list[RetrievalResult] = []
            for row in bm25_results[:k]:
                chunk_id, rank, content, doc_id, prec_id, judg_id, meta = row
                rank_f = float(rank)
                score = 1.0 / (1.0 + max(0.0, -rank_f))
                meta_dict = json.loads(meta) if isinstance(meta, str) else (meta or {})
                results.append(
                    RetrievalResult(
                        chunk_id=chunk_id,
                        content=content,
                        score=score,
                        legal_document_id=doc_id,
                        precedent_id=prec_id,
                        judgment_document_id=judg_id,
                        metadata=meta_dict,
                        cosine_similarity=0.5,
                    )
                )
            return results

        # Hybrid Reciprocal Rank Fusion (RRF)
        # Weighting: BM25 carries higher semantic specificity for Vietnamese legal terminology,
        # while dense provides complementary associative recall.
        w_dense = 0.2
        w_bm25 = 2.0

        rrf_scores: dict[str, float] = {}
        row_data: dict[str, tuple[str, str | None, str | None, str | None, Any]] = {}
        cosine_sims: dict[str, float] = {}

        # Fused top-candidates from dense (limit candidate set to top-30)
        for rank, row in enumerate(dense_results[:30]):
            chunk_id, distance, content, doc_id, prec_id, judg_id, meta = row
            dist_f = float(distance)
            row_data[chunk_id] = (content, doc_id, prec_id, judg_id, meta)
            cos_sim = max(0.0, min(1.0, 1.0 - (dist_f**2) / 2.0))
            cosine_sims[chunk_id] = cos_sim
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + w_dense / (60.0 + rank)

        # Fused top-candidates from BM25 (limit candidate set to top-30)
        for rank, row in enumerate(bm25_results[:30]):
            chunk_id, bm_rank, content, doc_id, prec_id, judg_id, meta = row
            if chunk_id not in row_data:
                row_data[chunk_id] = (content, doc_id, prec_id, judg_id, meta)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + w_bm25 / (60.0 + rank)

        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:k]

        results = []
        for cid in sorted_cids:
            content, doc_id, prec_id, judg_id, meta = row_data[cid]
            meta_dict = json.loads(meta) if isinstance(meta, str) else (meta or {})
            cos_sim = cosine_sims.get(cid, 0.5)
            results.append(
                RetrievalResult(
                    chunk_id=cid,
                    content=content,
                    score=rrf_scores[cid],
                    legal_document_id=doc_id,
                    precedent_id=prec_id,
                    judgment_document_id=judg_id,
                    metadata=meta_dict,
                    cosine_similarity=cos_sim,
                )
            )

        return results
