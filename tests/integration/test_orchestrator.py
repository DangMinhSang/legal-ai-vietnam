"""Integration test cho CaseAnalysisOrchestrator.

Kiểm tra toàn bộ luồng điều phối tích hợp:
1. Temporal Legal Engine xác định phiên bản luật áp dụng
2. Legal RAG truy vấn QPPL
3. Precedent Agent truy vấn án lệ
4. Similar Case Retrieval truy vấn bản án tương tự
5. First Instance Predictor dự đoán kết quả
6. Legal Consistency Checker kiểm tra tính nhất quán
"""

from __future__ import annotations

from datetime import date
import pytest

from src.db.models import LegalDocument, Precedent, JudgmentDocument
from src.legal_rag.chunker import Chunk
from src.legal_rag.indexer import LegalIndexer
from src.orchestration.orchestrator import CaseAnalysisOrchestrator
from tests.integration.test_rag_pipeline import DeterministicMockEmbedder


@pytest.mark.asyncio
async def test_case_analysis_orchestrator_end_to_end(db_session):
    """Kiểm tra toàn bộ luồng điều phối phân tích vụ án."""
    # 1. Chuẩn bị dữ liệu mẫu trong DB
    mock_embedder = DeterministicMockEmbedder(dim=768)
    indexer = LegalIndexer(dim=768)
    indexer._embedder = mock_embedder

    # QPPL: Điều 168 BLHS 2015
    doc = LegalDocument(
        title="Bộ luật Hình sự 2015",
        doc_type="law",
        doc_number="100/2015/QH13",
        status="active",
    )
    db_session.add(doc)
    await db_session.flush()

    content_law = "Điều 168. Tội cướp tài sản. Người nào dùng vũ lực, đe dọa dùng vũ lực ngay tức khắc chiếm đoạt tài sản."
    chunks_law = [
        Chunk(content=content_law, chunk_index=0, char_start=0, char_end=len(content_law), metadata={"article": "168"})
    ]
    await indexer.index_chunks(chunks_law, legal_document_id=doc.id, session=db_session)

    # Án lệ: Án lệ 01/2016/AL
    prec = Precedent(
        precedent_number="01/2016/AL",
        title="Án lệ về tội cướp tài sản dùng hung khí nguy hiểm",
        legal_issue_summary="Xác định tình tiết dùng hung khí nguy hiểm khi dùng dao khống chế",
    )
    db_session.add(prec)
    await db_session.flush()

    content_prec = "Tình huống án lệ: Dùng dao khống chế nạn nhân để cướp tài sản được coi là dùng hung khí nguy hiểm."
    chunks_prec = [
        Chunk(content=content_prec, chunk_index=0, char_start=0, char_end=len(content_prec), metadata={"type": "precedent"})
    ]
    await indexer.index_chunks(chunks_prec, precedent_id=prec.id, session=db_session)

    # Bản án: Bản án mẫu
    judgment = JudgmentDocument(
        judgment_number="01/2021/HSST",
        judgment_type="first_instance",
        legal_domain="criminal",
        full_text="Bản án hình sự sơ thẩm về tội cướp tài sản. Bị cáo dùng dao cướp điện thoại di động.",
    )
    db_session.add(judgment)
    await db_session.flush()

    content_judg = "Bản án hình sự sơ thẩm về tội cướp tài sản. Bị cáo dùng dao cướp điện thoại di động."
    chunks_judg = [
        Chunk(content=content_judg, chunk_index=0, char_start=0, char_end=len(content_judg), metadata={"type": "judgment"})
    ]
    await indexer.index_chunks(chunks_judg, judgment_document_id=judgment.id, session=db_session)

    # 2. Khởi tạo Orchestrator với mock embedder
    orchestrator = CaseAnalysisOrchestrator()
    orchestrator.legal_retriever._embedder = mock_embedder
    orchestrator.precedent_retriever.retriever._embedder = mock_embedder
    orchestrator.case_retriever.retriever._embedder = mock_embedder

    # 3. Phân tích vụ án
    query = "Hành vi dùng dao khống chế nạn nhân để cướp tài sản tại TP.HCM"
    offense_date = date(2021, 3, 15)
    judgment_date = date(2021, 6, 20)

    output = await orchestrator.analyze_case(
        case_description=query,
        incident_date=offense_date,
        judgment_date=judgment_date,
        session=db_session,
        case_id="case_test_001",
        input_features={
            "num_facts": 4.0,
            "num_aggravating": 1.0,
            "num_mitigating": 2.0,
        },
    )

    # 4. Kiểm tra kết quả
    assert output.case_id == "case_test_001"

    # Kiểm tra Temporal Legal Reasoning
    assert "document_number" in output.temporal_analysis
    assert output.temporal_analysis["document_number"] == "100/2015/QH13"
    assert output.temporal_analysis["selected_basis"] == "offense_date"
    assert len(output.temporal_analysis["citations"]) > 0

    # Kiểm tra Legal RAG
    assert len(output.relevant_laws) >= 1
    assert output.relevant_laws[0]["legal_document_id"] == doc.id

    # Kiểm tra Precedent Agent
    assert len(output.relevant_precedents) >= 1
    assert output.relevant_precedents[0]["precedent_id"] == prec.id

    # Kiểm tra Similar Cases
    assert len(output.similar_cases) >= 1
    assert output.similar_cases[0]["judgment_document_id"] == judgment.id

    # Kiểm tra Prediction
    assert "predicted_outcome" in output.predicted_outcome
    assert output.predicted_outcome["predicted_outcome"] in ["guilty", "not_guilty"]
    assert "probabilities" in output.predicted_outcome

    # Kiểm tra Consistency
    assert isinstance(output.consistency_warnings, list)


@pytest.mark.asyncio
async def test_case_analysis_orchestrator_temporal_retroactivity():
    """Kiểm tra xử lý thời gian theo Điều 7 BLHS 2015: hành vi trước 2018."""
    orchestrator = CaseAnalysisOrchestrator()

    # Hành vi phạm tội năm 2016 (trước ngày BLHS 2015 có hiệu lực 01/01/2018)
    # Xét xử năm 2019
    offense_date = date(2016, 5, 10)
    judgment_date = date(2019, 2, 20)

    output = await orchestrator.analyze_case(
        case_description="Hành vi lừa đảo chiếm đoạt tài sản xảy ra năm 2016",
        incident_date=offense_date,
        judgment_date=judgment_date,
    )

    # BLHS 1999 (15/1999/QH10) phải được chọn theo nguyên tắc thời điểm phạm tội
    assert output.temporal_analysis["document_number"] == "15/1999/QH10"
    assert output.temporal_analysis["selected_basis"] == "offense_date"
    # Cần có lưu ý chuyển tiếp về Điều 7 BLHS 2015
    assert output.temporal_analysis["transitional_note"] is not None
    assert "Điều 7 BLHS 2015" in output.temporal_analysis["transitional_note"]

