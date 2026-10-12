"""Data leakage detection and prevention utilities.

Ensures strict separation between:
1. Input features and outcome labels (both for first instance and appeal).
2. Train, validation, and test splits (grouped by case_id).
3. Temporal splits (train strictly precedes test chronologically).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


FIRST_INSTANCE_OUTCOME_FIELDS = frozenset({
    "verdict",
    "sentence_years",
    "sentence_duration",
    "sentence_type",
    "fine_amount",
    "outcome",
    "first_instance_verdict",
    "first_instance_sentence",
    "actual_outcome",
    "is_guilty",
})

APPELLATE_OUTCOME_FIELDS = frozenset({
    "appellate_outcome",
    "appeal_result",
    "appellate_verdict",
    "is_upheld",
    "is_overturned",
    "modified_sentence",
    "appeal_judgment_id",
})


def build_first_instance_features(case_data: dict[str, Any]) -> dict[str, Any]:
    """Construct feature set for first-instance outcome prediction.

    Guarantees no outcome leak: strictly strips verdict, sentence, and outcome fields.
    """
    return {
        k: v
        for k, v in case_data.items()
        if k not in FIRST_INSTANCE_OUTCOME_FIELDS and not k.startswith("outcome_")
    }


def build_appeal_features(case_data: dict[str, Any]) -> dict[str, Any]:
    """Construct feature set for appellate outcome prediction.

    Allows first-instance outcome fields as valid input, but strictly excludes
    all appellate outcomes to prevent future information leakage.
    """
    return {
        k: v
        for k, v in case_data.items()
        if k not in APPELLATE_OUTCOME_FIELDS and not k.startswith("appellate_")
    }


def split_cases_by_case_id(
    documents: list[dict[str, Any]],
    train_ratio: float = 0.8,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Group documents by case_id to prevent cross-split contamination."""
    cases_map: dict[str, list[dict[str, Any]]] = {}
    for doc in documents:
        cid = doc.get("case_id") or doc.get("id") or "default"
        cases_map.setdefault(cid, []).append(doc)

    unique_case_ids = list(cases_map.keys())
    cutoff = int(len(unique_case_ids) * train_ratio)
    train_case_ids = set(unique_case_ids[:cutoff])

    train_set: list[dict[str, Any]] = []
    test_set: list[dict[str, Any]] = []

    for cid, docs in cases_map.items():
        if cid in train_case_ids:
            train_set.extend(docs)
        else:
            test_set.extend(docs)

    return train_set, test_set


def temporal_split(
    cases: list[dict[str, Any]],
    split_date: str | date | datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split cases chronologically based on judgment_date or incident_date."""
    if isinstance(split_date, str):
        split_dt = datetime.fromisoformat(split_date)
    elif isinstance(split_date, date) and not isinstance(split_date, datetime):
        split_dt = datetime(split_date.year, split_date.month, split_date.day)
    else:
        split_dt = split_date

    train_cases: list[dict[str, Any]] = []
    test_cases: list[dict[str, Any]] = []

    for c in cases:
        c_date = c.get("judgment_date") or c.get("date")
        if isinstance(c_date, str):
            c_dt = datetime.fromisoformat(c_date)
        elif isinstance(c_date, date) and not isinstance(c_date, datetime):
            c_dt = datetime(c_date.year, c_date.month, c_date.day)
        else:
            c_dt = c_date

        if c_dt is None or c_dt < split_dt:
            train_cases.append(c)
        else:
            test_cases.append(c)

    return train_cases, test_cases
