"""Legal AI Vietnam — package gốc.

Hệ thống AI hỗ trợ nghiên cứu pháp lý và dự đoán kết quả vụ án
trong lĩnh vực luật Việt Nam.

Các sub-package chính:
- ingestion: thu thập dữ liệu từ VBPL, toà án, HuggingFace
- document_parser: phân tích PDF, HTML, DOCX
- fact_extraction: trích xuất tình tiết từ hồ sơ vụ án
- legal_rag: indexing và retrieval văn bản pháp luật
- precedent_agent: tìm kiếm và so khớp án lệ
- case_retrieval: truy vấn hồ sơ vụ án tương tự
- temporal_legal_engine: quản lý phiên bản luật theo thời gian
- first_instance: dự đoán kết quả sơ thẩm
- appeal_prediction: dự đoán kết quả phúc thẩm
- orchestration: điều phối các agent
- validation: kiểm tra tính nhất quán đầu ra
- evaluation: đánh giá hiệu suất hệ thống
- api: FastAPI endpoints
- db: database layer (SQLite + sqlite-vec)
"""

__version__ = "0.1.0"
__author__ = "UIT Legal AI Team"
