"""Sub-package precedent_agent: tìm kiếm và so khớp án lệ chính thức.

Hệ thống tra cứu án lệ của TANDTC Việt Nam dựa trên:
- Semantic similarity của tình tiết pháp lý
- So khớp lĩnh vực pháp lý
- Ranking theo độ tương đồng và năm ban hành

Các module:
- indexer: index các án lệ vào sqlite-vec
- retriever: tìm kiếm án lệ tương tự cho vụ án mới
"""

from src.precedent_agent.indexer import PrecedentIndexer
from src.precedent_agent.retriever import PrecedentRetriever

__all__ = ["PrecedentIndexer", "PrecedentRetriever"]
