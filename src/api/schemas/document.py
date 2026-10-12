"""Document management request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response returned upon file upload."""

    document_id: str
    filename: str
    status: str
    page_count: int | None = None
    extracted_text_length: int
    parse_method: str  # text_extraction | ocr | mixed
    warnings: list[str] = Field(default_factory=list)


class DocumentListItem(BaseModel):
    """Brief summary item in document list."""

    id: str
    filename: str
    processing_status: str
    page_count: int | None = None
    linked_case_id: str | None = None
    created_at: str


class DocumentDetailResponse(BaseModel):
    """Full detail of an uploaded document including extracted text."""

    id: str
    filename: str
    processing_status: str
    page_count: int | None = None
    extracted_text: str | None = None
    extracted_text_length: int
    parse_method: str
    warnings: list[str] = Field(default_factory=list)
    linked_case_id: str | None = None
    created_at: str
