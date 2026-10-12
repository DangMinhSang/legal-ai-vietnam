"""Sub-package evaluation: đánh giá hiệu suất toàn bộ hệ thống.

Các metric được tính:
- Retrieval: Precision@k, Recall@k, NDCG@k, MRR
- Prediction: Accuracy, F1-macro, F1-weighted, ROC-AUC, Calibration
- End-to-end: Answer relevance, Faithfulness, Citation accuracy

Kết quả lưu vào bảng evaluation_results trong DB.

Các module:
- metrics: hàm tính toán từng loại metric
"""

from src.evaluation.metrics import RetrievalMetrics, PredictionMetrics

__all__ = ["RetrievalMetrics", "PredictionMetrics"]
