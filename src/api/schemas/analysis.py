"""AI analysis request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request to analyze a judgment document."""

    judgment_id: str
    analysis_types: list[str] = Field(
        default_factory=lambda: ["entity_extraction", "crime_classification"]
    )
    include_similar_cases: bool = True
    include_legal_provisions: bool = True


class AnalysisResult(BaseModel):
    """Structured AI analysis result."""

    judgment_id: str
    analysis_type: str
    model_used: str
    result: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    processing_time_ms: int = 0
    warnings: list[str] = Field(default_factory=list)
    uncertainty_flags: list[str] = Field(default_factory=list)


class SimilarCasesRequest(BaseModel):
    """Request to find similar court cases."""

    judgment_id: str | None = None
    text: str | None = None
    top_k: int = 5


class SimilarCaseItem(BaseModel):
    """Summary item for a retrieved similar case."""

    judgment_id: str
    judgment_number: str | None = None
    title: str | None = None
    similarity_score: float
    summary: str | None = None


class LegalProvisionsRequest(BaseModel):
    """Request to find relevant legal provisions given fact descriptions."""

    text: str
    top_k: int = 5


class LegalProvisionItem(BaseModel):
    """Relevant law article with citation and explanation."""

    article: str
    law_name: str
    content: str
    relevance_score: float
    source_citation: str


class CaseOrchestrationRequest(BaseModel):
    """Yêu cầu phân tích và dự đoán xét xử vụ án hình sự toàn diện."""

    case_description: str = Field(description="Mô tả tóm tắt tình tiết vụ án")
    incident_date: str | None = Field(default=None, description="Ngày xảy ra hành vi phạm tội (YYYY-MM-DD)")
    judgment_date: str | None = Field(default=None, description="Ngày xét xử vụ án (YYYY-MM-DD)")
    case_id: str | None = Field(default=None, description="Mã vụ án (nếu có)")
    input_features: dict[str, float] | None = Field(default=None, description="Đặc trưng đầu vào khách quan")


class CaseOrchestrationResponse(BaseModel):
    """Kết quả phân tích toàn diện từ Orchestrator đa tác tử."""

    case_id: str | None = None
    case_description: str
    temporal_analysis: dict[str, Any] = Field(default_factory=dict)
    relevant_laws: list[dict[str, Any]] = Field(default_factory=list)
    relevant_precedents: list[dict[str, Any]] = Field(default_factory=list)
    similar_cases: list[dict[str, Any]] = Field(default_factory=list)
    predicted_outcome: dict[str, Any] = Field(default_factory=dict)
    consistency_warnings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    processing_time_ms: int = 0


class WebAnalysisRequest(BaseModel):
    """Yêu cầu phân tích từ giao diện web (hỗ trợ cả 2 khung hoặc 1 khung tự do)."""

    personal_info: str = Field(default="", description="1. Thông tin cá nhân (Bị cáo, Bị hại, nhiều người)")
    case_info: str = Field(default="", description="2. Thông tin vụ án (Hành vi, thời gian, công cụ, hậu quả)")
    full_text: str = Field(default="", description="Toàn văn vụ án / cáo trạng tự do (tùy chọn)")


class AutoSplitRequest(BaseModel):
    """Yêu cầu tự động phân tách văn bản tự do thành 2 phần."""

    text: str = Field(description="Toàn văn hồ sơ, cáo trạng hoặc tóm tắt vụ việc")


class AutoSplitResponse(BaseModel):
    """Kết quả tự động phân tách thành 2 khung nhập liệu."""

    personal_info: str
    case_info: str
    parties_count: int = 0



