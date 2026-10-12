"""Sub-package appeal_prediction: dự đoán kết quả xét xử phúc thẩm.

Mô hình dự đoán khả năng thành công của kháng cáo dựa trên:
- Kết quả và luận cứ sơ thẩm
- Lý do kháng cáo (grounds)
- Tỷ lệ lịch sử theo loại tội / lĩnh vực
- Sai sót thủ tục tố tụng (nếu phát hiện)

Output: xác suất cho upheld / overturned / modified / dismissed

Các module:
- feature_builder: xây dựng feature vector từ kết quả sơ thẩm + kháng cáo
- predictor: LightGBM classifier cho dự đoán phúc thẩm
"""

from src.appeal_prediction.predictor import AppealPredictor
from src.appeal_prediction.feature_builder import AppealFeatureBuilder

__all__ = ["AppealPredictor", "AppealFeatureBuilder"]
