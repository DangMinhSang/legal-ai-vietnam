"""Sub-package orchestration: điều phối luồng phân tích vụ án.

Orchestrator kết nối tất cả các component thành một pipeline hoàn chỉnh:
1. Nhận yêu cầu phân tích vụ án
2. Trích xuất tình tiết (fact_extraction)
3. Xác định luật áp dụng (temporal_legal_engine)
4. Tìm văn bản pháp luật liên quan (legal_rag)
5. Tìm án lệ tương tự (precedent_agent)
6. Tìm vụ án tương tự (case_retrieval)
7. Dự đoán kết quả (first_instance / appeal_prediction)
8. Kiểm tra nhất quán (validation)
9. Tổng hợp và trả kết quả

Các module:
- orchestrator: lớp CaseAnalysisOrchestrator điều phối toàn bộ
"""

from src.orchestration.orchestrator import CaseAnalysisOrchestrator

__all__ = ["CaseAnalysisOrchestrator"]
