"""Sub-package first_instance: dự đoán kết quả xét xử sơ thẩm.

Mô hình dự đoán dựa trên:
- Tình tiết vụ án (tăng nặng, giảm nhẹ)
- Lĩnh vực pháp lý và tội danh
- Toà án xét xử và thẩm phán (nếu có)
- Thống kê từ các vụ án tương tự trong lịch sử

Output: xác suất cho từng kết quả (guilty/not_guilty, mức án, bồi thường)

Các module:
- feature_builder: xây dựng feature vector từ CaseFact và metadata
- predictor: scikit-learn / XGBoost classifier + calibration
"""

from src.first_instance.predictor import FirstInstancePredictor
from src.first_instance.feature_builder import FirstInstanceFeatureBuilder

__all__ = ["FirstInstancePredictor", "FirstInstanceFeatureBuilder"]
