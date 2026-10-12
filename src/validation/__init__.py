"""Sub-package validation: kiểm tra tính nhất quán đầu ra của hệ thống.

Thực hiện các kiểm tra:
- Điều luật trích dẫn có tồn tại và còn hiệu lực không?
- Kết quả dự đoán có nhất quán với tình tiết không?
- Thông tin truy xuất có liên quan đến câu hỏi không?
- Phát hiện hallucination từ LLM (citation checking)

Các module:
- consistency_checker: kiểm tra cross-module consistency
"""

from src.validation.consistency_checker import ConsistencyChecker
from src.validation.leakage import (
    build_appeal_features,
    build_first_instance_features,
    split_cases_by_case_id,
    temporal_split,
)

__all__ = [
    "ConsistencyChecker",
    "build_first_instance_features",
    "build_appeal_features",
    "split_cases_by_case_id",
    "temporal_split",
]
