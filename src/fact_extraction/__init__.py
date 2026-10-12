"""Fact extraction from Vietnamese legal judgments using LLM."""

from src.fact_extraction.schemas import (
    CaseFacts,
    DefendantInfo,
    ExtractedField,
    ExtractionStatus,
    JudgmentOutcomeSchema,
)
from src.fact_extraction.extractor import CaseFactExtractor

__all__ = [
    "CaseFacts",
    "DefendantInfo",
    "ExtractedField",
    "ExtractionStatus",
    "JudgmentOutcomeSchema",
    "CaseFactExtractor",
]
