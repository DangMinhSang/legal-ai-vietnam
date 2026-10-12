"""Pydantic schemas package for Legal AI Vietnam API."""

from src.api.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    LegalProvisionItem,
    LegalProvisionsRequest,
    SimilarCaseItem,
    SimilarCasesRequest,
)
from src.api.schemas.common import APIResponse, PaginatedResponse
from src.api.schemas.document import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentUploadResponse,
)

__all__ = [
    "APIResponse",
    "PaginatedResponse",
    "DocumentUploadResponse",
    "DocumentListItem",
    "DocumentDetailResponse",
    "AnalysisRequest",
    "AnalysisResult",
    "SimilarCasesRequest",
    "SimilarCaseItem",
    "LegalProvisionsRequest",
    "LegalProvisionItem",
]
