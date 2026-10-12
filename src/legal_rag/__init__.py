"""Sub-package legal_rag: indexing và retrieval văn bản pháp luật.

Pipeline:
1. chunker: chia văn bản thành đoạn nhỏ phù hợp với context window
2. indexer: tạo embedding (fastembed) và lưu vào sqlite-vec
3. retriever: hybrid search (dense + BM25) và reranking

Các module:
- chunker: chiến lược chunking theo cấu trúc pháp lý Việt Nam
- indexer: tạo và lưu trữ vector embedding
- retriever: tìm kiếm ngữ nghĩa và tái xếp hạng kết quả
"""

from src.legal_rag.chunker import LegalChunker
from src.legal_rag.indexer import LegalIndexer
from src.legal_rag.retriever import LegalRetriever

__all__ = ["LegalChunker", "LegalIndexer", "LegalRetriever"]
