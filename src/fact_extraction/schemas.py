"""Pydantic schemas for structured fact extraction from Vietnamese legal judgments."""


from pydantic import BaseModel, Field, model_validator
from typing import Optional
from enum import Enum


class ExtractionStatus(str, Enum):
    EXTRACTED = "extracted"
    INFERRED = "inferred"
    MISSING = "missing"
    CONFLICTING = "conflicting"


class ExtractedField(BaseModel):
    value: Optional[str] = None
    status: ExtractionStatus = ExtractionStatus.MISSING
    source_page: Optional[int] = None
    source_paragraph: Optional[str] = None
    confidence: Optional[float] = None

    @model_validator(mode="after")
    def validate_missing_value(self) -> "ExtractedField":
        if self.status == ExtractionStatus.MISSING and self.value is not None:
            raise ValueError("Field with missing status must have None value")
        return self


def _default_missing() -> ExtractedField:
    return ExtractedField(status=ExtractionStatus.MISSING, value=None)


class CaseFacts(BaseModel):
    """Tình tiết vụ án đã trích xuất - mọi field đều có trạng thái rõ ràng"""
    case_number: ExtractedField = Field(default_factory=_default_missing)
    court_name: ExtractedField = Field(default_factory=_default_missing)
    court_level: ExtractedField = Field(default_factory=_default_missing)  # district/provincial/high/supreme
    judgment_date: ExtractedField = Field(default_factory=_default_missing)  # ISO 8601
    proceeding_stage: ExtractedField = Field(default_factory=_default_missing)  # first_instance/appeal

    # Tội danh
    charges: list[ExtractedField] = Field(default_factory=list)
    applied_articles: list[ExtractedField] = Field(default_factory=list)

    # Thời gian
    offense_date: ExtractedField = Field(default_factory=_default_missing)
    offense_end_date: ExtractedField = Field(default_factory=_default_missing)  # Nếu hành vi kéo dài

    # Bị cáo (tóm tắt - chi tiết trong Defendant model)
    defendant_count: ExtractedField = Field(default_factory=_default_missing)

    # Hậu quả
    damage_description: ExtractedField = Field(default_factory=_default_missing)
    damage_value_vnd: ExtractedField = Field(default_factory=_default_missing)

    # Tình tiết
    aggravating_factors: list[ExtractedField] = Field(default_factory=list)
    mitigating_factors: list[ExtractedField] = Field(default_factory=list)

    # Kết quả sơ thẩm
    first_instance_verdict: ExtractedField = Field(default_factory=_default_missing)
    first_instance_sentence: ExtractedField = Field(default_factory=_default_missing)

    # Kháng cáo (nếu có)
    has_appeal: ExtractedField = Field(default_factory=_default_missing)
    appeal_type: ExtractedField = Field(default_factory=_default_missing)
    appeal_scope: ExtractedField = Field(default_factory=_default_missing)

    # Kết quả phúc thẩm (nếu có)
    appellate_outcome: ExtractedField = Field(default_factory=_default_missing)

    class Config:
        use_enum_values = True


class DefendantInfo(BaseModel):
    name: ExtractedField = Field(default_factory=_default_missing)
    birth_year: ExtractedField = Field(default_factory=_default_missing)
    gender: ExtractedField = Field(default_factory=_default_missing)
    prior_convictions: ExtractedField = Field(default_factory=_default_missing)
    role_in_crime: ExtractedField = Field(default_factory=_default_missing)
    sentence_type: ExtractedField = Field(default_factory=_default_missing)
    sentence_duration: ExtractedField = Field(default_factory=_default_missing)  # e.g., "3 năm 6 tháng"
    sentence_years: ExtractedField = Field(default_factory=_default_missing)    # Numeric
    fine_amount: ExtractedField = Field(default_factory=_default_missing)
    suspended: ExtractedField = Field(default_factory=_default_missing)  # bool


class JudgmentOutcomeSchema(BaseModel):
    """Kết quả xét xử đã xác minh"""
    verdict: str  # co_toi/vo_toi/dinh_chi
    offense_labels: list[str]
    applied_provisions: list[str]  # ["Điều 123 khoản 1 BLHS 2015"]
    principal_penalties: list[str]
    supplementary_penalties: list[str] = Field(default_factory=list)
    suspended_sentence: Optional[bool] = None
    appellate_outcome: Optional[str] = None
    annotation_status: str = "unverified"
