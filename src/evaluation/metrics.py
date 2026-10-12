"""Metrics evaluation cho toàn bộ hệ thống Legal AI Vietnam."""

from __future__ import annotations

import numpy as np


class RetrievalMetrics:
    """Tính các metric đánh giá chất lượng truy vấn RAG."""

    @staticmethod
    def precision_at_k(actual_relevant_ids: set[str], retrieved_ids: list[str], k: int) -> float:
        """Tính Precision@k."""
        if not retrieved_ids or k <= 0:
            return 0.0
        top_k = retrieved_ids[:k]
        hits = sum(1 for doc_id in top_k if doc_id in actual_relevant_ids)
        return hits / float(k)

    @staticmethod
    def recall_at_k(actual_relevant_ids: set[str], retrieved_ids: list[str], k: int) -> float:
        """Tính Recall@k."""
        if not actual_relevant_ids or k <= 0:
            return 0.0
        top_k = retrieved_ids[:k]
        hits = sum(1 for doc_id in top_k if doc_id in actual_relevant_ids)
        return hits / float(len(actual_relevant_ids))

    @staticmethod
    def mrr(actual_relevant_ids: set[str], retrieved_ids: list[str]) -> float:
        """Tính Mean Reciprocal Rank (MRR)."""
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in actual_relevant_ids:
                return 1.0 / rank
        return 0.0


class PredictionMetrics:
    """Tính các metric đánh giá mô hình dự đoán kết quả xét xử."""

    @staticmethod
    def accuracy(y_true: list[str], y_pred: list[str]) -> float:
        if not y_true:
            return 0.0
        return float(np.mean([1.0 if yt == yp else 0.0 for yt, yp in zip(y_true, y_pred)]))
