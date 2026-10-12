"""Lớp cơ sở cho fact extractor.

Định nghĩa interface chung cho tất cả extractor implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.fact_extraction.schemas import ExtractionResult


class BaseExtractor(ABC):
    """Lớp cơ sở trừu tượng cho fact extractor.

    Subclass phải implement extract().
    """

    @abstractmethod
    async def extract(self, text: str, context: str | None = None) -> ExtractionResult:
        """Trích xuất tình tiết từ văn bản hồ sơ vụ án.

        Args:
            text: Văn bản hồ sơ cần trích xuất
            context: Thông tin bổ sung về vụ án (tuỳ chọn)

        Returns:
            ExtractionResult chứa danh sách tình tiết
        """
        ...

    async def extract_batch(
        self, texts: list[str], context: str | None = None
    ) -> list[ExtractionResult]:
        """Trích xuất từ nhiều văn bản (mặc định tuần tự, có thể override song song).

        Args:
            texts: Danh sách văn bản cần trích xuất
            context: Thông tin bổ sung dùng chung cho tất cả

        Returns:
            Danh sách ExtractionResult tương ứng với mỗi text
        """
        results: list[ExtractionResult] = []
        for text in texts:
            result = await self.extract(text, context)
            results.append(result)
        return results
