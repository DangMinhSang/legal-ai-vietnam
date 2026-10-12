"""Orchestrator điều phối toàn bộ luồng phân tích và dự đoán xét xử vụ án hình sự.

Tuân thủ nghiêm ngặt các nguyên tắc từ Master Prompt:
1. Phân biệt rõ ràng 3 nguồn tri thức:
   - Văn bản quy phạm pháp luật (QPPL)
   - Án lệ chính thức của Hội đồng Thẩm phán TANDTC
   - Bản án thông thường từ toà án
2. Temporal Legal Reasoning:
   - Xác định phiên bản luật áp dụng theo Điều 7 BLHS 2015
   - Nguyên tắc bất hồi tố và áp dụng quy định có lợi cho người phạm tội
3. Không rò rỉ nhãn (No label leakage):
   - Tuyệt đối không đưa kết quả sơ thẩm vào feature đầu vào sơ thẩm
4. Kiểm tra tính nhất quán (Legal Consistency Checking):
   - Đảm bảo trích dẫn, khung hình phạt và logic pháp lý không tự mâu thuẫn
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.case_retrieval.retriever import CaseRetriever
from src.first_instance.feature_builder import FirstInstanceFeatureBuilder
from src.first_instance.predictor import FirstInstancePredictor
from src.legal_rag.retriever import LegalRetriever
from src.precedent_agent.retriever import PrecedentRetriever
from src.temporal_legal_engine.version_selector import (
    LegalVersionResult,
    TemporalVersionSelector,
)
from src.validation.consistency_checker import ConsistencyChecker

logger = logging.getLogger(__name__)


@dataclass
class CaseAnalysisOutput:
    """Kết quả phân tích toàn diện một vụ án hình sự."""

    case_id: str | None = None
    case_description: str = ""
    temporal_analysis: dict[str, Any] = field(default_factory=dict)
    relevant_laws: list[dict[str, Any]] = field(default_factory=list)
    relevant_precedents: list[dict[str, Any]] = field(default_factory=list)
    similar_cases: list[dict[str, Any]] = field(default_factory=list)
    predicted_outcome: dict[str, Any] = field(default_factory=dict)
    consistency_warnings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CaseAnalysisOrchestrator:
    """Điều phối toàn bộ luồng phân tích từ RAG, Án lệ, Temporal Engine đến Prediction."""

    def __init__(self) -> None:
        self.temporal_selector = TemporalVersionSelector()
        self.legal_retriever = LegalRetriever()
        self.precedent_retriever = PrecedentRetriever()
        self.case_retriever = CaseRetriever()
        self.first_instance_predictor = FirstInstancePredictor()
        self.consistency_checker = ConsistencyChecker()

    async def analyze_case(
        self,
        case_description: str,
        incident_date: datetime | date | None = None,
        judgment_date: datetime | date | None = None,
        session: AsyncSession | None = None,
        case_id: str | None = None,
        input_features: dict[str, float] | None = None,
    ) -> CaseAnalysisOutput:
        """Phân tích vụ án hoàn chỉnh với đầy đủ các thành phần.

        Args:
            case_description: Mô tả tình tiết vụ án
            incident_date: Ngày xảy ra hành vi phạm tội (nếu có)
            judgment_date: Ngày xét xử vụ án (nếu có)
            session: AsyncSession SQLAlchemy
            case_id: Mã định danh vụ án (nếu có)
            input_features: Đặc trưng đầu vào đã làm sạch (nếu có)
        """
        output = CaseAnalysisOutput(
            case_id=case_id,
            case_description=case_description,
        )

        # -------------------------------------------------------------------
        # 1. Temporal Legal Reasoning: Xác định phiên bản luật áp dụng
        # -------------------------------------------------------------------
        try:
            # Danh sách các phiên bản BLHS cơ bản để giải quyết thời gian
            available_blhs_versions = [
                {
                    "id": "BLHS_1999",
                    "document_number": "15/1999/QH10",
                    "effective_from": date(2000, 7, 1),
                    "effective_to": date(2017, 12, 31),
                },
                {
                    "id": "BLHS_2015",
                    "document_number": "100/2015/QH13",
                    "effective_from": date(2018, 1, 1),
                    "effective_to": None,
                },
            ]

            temporal_res = self.temporal_selector.select_version(
                document_id="BLHS_2015",
                offense_date=incident_date,
                judgment_date=judgment_date,
                available_versions=available_blhs_versions,
            )

            output.temporal_analysis = {
                "document_id": temporal_res.document_id,
                "document_number": temporal_res.document_number,
                "selected_basis": temporal_res.selected_version_basis.value,
                "effective_from": temporal_res.effective_from,
                "effective_to": temporal_res.effective_to,
                "citations": temporal_res.citations,
                "transitional_note": temporal_res.transitional_note,
                "uncertainty": temporal_res.uncertainty,
                "uncertainty_reason": temporal_res.uncertainty_reason,
                "requires_expert_review": temporal_res.requires_expert_review,
            }

            if temporal_res.uncertainty and temporal_res.uncertainty_reason:
                output.warnings.append(f"Temporal uncertainty: {temporal_res.uncertainty_reason}")

        except Exception as e:
            logger.error("Temporal resolution error: %s", e)
            output.warnings.append(f"Temporal resolution error: {e}")

        # -------------------------------------------------------------------
        # 2. Truy vấn văn bản pháp luật liên quan (Legal RAG)
        # -------------------------------------------------------------------
        if session is not None:
            try:
                legal_chunks = await self.legal_retriever.retrieve(case_description, session, top_k=10)
                output.relevant_laws = [
                    {
                        "chunk_id": c.chunk_id,
                        "content": c.content,
                        "score": c.score,
                        "legal_document_id": c.legal_document_id,
                        "metadata": c.metadata,
                    }
                    for c in legal_chunks
                    if c.legal_document_id is not None
                ][:5]
            except Exception as e:
                logger.error("Legal retrieval error: %s", e)
                output.warnings.append(f"Legal retrieval error: {e}")

            # -------------------------------------------------------------------
            # 3. Truy vấn án lệ tương tự (Precedent Agent)
            # -------------------------------------------------------------------
            try:
                precedents = await self.precedent_retriever.find_similar_precedents(
                    case_description, session, top_k=3
                )
                output.relevant_precedents = [
                    {
                        "chunk_id": p.chunk_id,
                        "content": p.content,
                        "score": p.score,
                        "precedent_id": p.precedent_id,
                        "metadata": p.metadata,
                    }
                    for p in precedents
                ]
            except Exception as e:
                logger.error("Precedent retrieval error: %s", e)
                output.warnings.append(f"Precedent retrieval error: {e}")

            # -------------------------------------------------------------------
            # 4. Truy vấn bản án thông thường tương đồng (Similar Case Retrieval)
            # -------------------------------------------------------------------
            try:
                cases = await self.case_retriever.find_similar_cases(
                    case_description, session, top_k=3
                )
                output.similar_cases = [
                    {
                        "chunk_id": c.chunk_id,
                        "content": c.content,
                        "score": c.score,
                        "judgment_document_id": c.judgment_document_id,
                        "metadata": c.metadata,
                    }
                    for c in cases
                ]
            except Exception as e:
                logger.error("Similar case retrieval error: %s", e)
                output.warnings.append(f"Similar case retrieval error: {e}")

        # -------------------------------------------------------------------
        # 5. Dự đoán kết quả xét xử sơ thẩm (First-instance Prediction)
        # -------------------------------------------------------------------
        features = input_features or {
            "num_facts": 3.0,
            "num_aggravating": 1.0,
            "num_mitigating": 1.0,
        }
        try:
            output.predicted_outcome = self.first_instance_predictor.predict(features)
        except Exception as e:
            logger.error("Prediction error: %s", e)
            output.warnings.append(f"Prediction error: {e}")

        # -------------------------------------------------------------------
        # 6. Kiểm tra tính nhất quán pháp lý (Legal Consistency Checking)
        # -------------------------------------------------------------------
        try:
            pred_outcome = output.predicted_outcome.get("predicted_outcome", "unknown")
            agg_cnt = int(features.get("num_aggravating", 0))
            mit_cnt = int(features.get("num_mitigating", 0))

            logic_warnings = self.consistency_checker.validate_prediction_logic(
                outcome=pred_outcome,
                aggravating_count=agg_cnt,
                mitigating_count=mit_cnt,
            )
            output.consistency_warnings.extend(logic_warnings)

            # Kiểm tra tính nhất quán về thời gian nếu có ngày
            if incident_date and output.temporal_analysis:
                eff_from = output.temporal_analysis.get("effective_from")
                temporal_warnings = self.consistency_checker.validate_temporal_consistency(
                    offense_date=incident_date,
                    law_effective_date=eff_from,
                )
                output.consistency_warnings.extend(temporal_warnings)

        except Exception as e:
            logger.error("Consistency check error: %s", e)
            output.warnings.append(f"Consistency check error: {e}")

        return output
