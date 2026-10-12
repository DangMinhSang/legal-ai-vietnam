"""Sub-package case_retrieval: truy vấn hồ sơ vụ án tương tự.

Tìm kiếm các bản án đã xét xử có tình tiết tương đồng với vụ án
đang phân tích, phục vụ cho:
- Dự đoán kết quả (tìm precedent thực tế)
- Phân tích rủi ro pháp lý
- Gợi ý chiến lược bào chữa

Các module:
- indexer: index bản án và tình tiết vào sqlite-vec
- retriever: tìm kiếm vụ án tương tự theo tình tiết và lĩnh vực
"""

from src.case_retrieval.indexer import CaseIndexer
from src.case_retrieval.retriever import CaseRetriever

__all__ = ["CaseIndexer", "CaseRetriever"]
