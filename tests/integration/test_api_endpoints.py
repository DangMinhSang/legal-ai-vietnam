"""Integration tests for FastAPI endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test /health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_detailed_health(client: AsyncClient):
    """Test /health/detailed endpoint."""
    response = await client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_document_upload_and_list(client: AsyncClient):
    """Test uploading a text document and listing documents."""
    file_content = b"BAN AN HINH SU SO THAM. Bi cao Nguyen Van A pham toi trom cap tai san."
    files = {"file": ("test_ban_an.txt", file_content, "text/plain")}

    # 1. Upload
    response = await client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201
    upload_data = response.json()
    assert "document_id" in upload_data
    doc_id = upload_data["document_id"]
    assert upload_data["filename"] == "test_ban_an.txt"
    assert upload_data["extracted_text_length"] > 0

    # 2. Get detail
    detail_res = await client.get(f"/api/v1/documents/{doc_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["success"] is True
    assert detail_data["data"]["id"] == doc_id
    assert "Nguyen Van A" in detail_data["data"]["extracted_text"]

    # 3. List documents
    list_res = await client.get("/api/v1/documents/")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == doc_id for item in list_data["items"])

    # 4. Soft delete
    del_res = await client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


@pytest.mark.asyncio
async def test_analysis_endpoints(client: AsyncClient):
    """Test analysis endpoints."""
    # 1. Upload sample document first
    file_content = b"BAN AN HINH SU: Bi cao Nguyen Van B pham toi trom cap tai san theo Dieu 173 BLHS."
    files = {"file": ("ban_an_b.txt", file_content, "text/plain")}
    up_res = await client.post("/api/v1/documents/upload", files=files)
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    # 2. Extract facts
    extract_res = await client.post(
        "/api/v1/analysis/extract",
        json={"judgment_id": doc_id},
    )
    assert extract_res.status_code == 200
    extract_data = extract_res.json()
    assert extract_data["success"] is True
    assert extract_data["data"]["judgment_id"] == doc_id

    # 3. Similar cases
    similar_res = await client.post(
        "/api/v1/analysis/similar-cases",
        json={"judgment_id": doc_id, "top_k": 3},
    )
    assert similar_res.status_code == 200
    similar_data = similar_res.json()
    assert similar_data["success"] is True
    assert len(similar_data["data"]) > 0

    # 4. Legal provisions
    prov_res = await client.post(
        "/api/v1/analysis/legal-provisions",
        json={"text": "Hanh vi trom cap tai san xe may tri gia 30 trieu dong", "top_k": 3},
    )
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert prov_data["success"] is True
    assert len(prov_data["data"]) > 0

    # 5. Get results
    results_res = await client.get(f"/api/v1/analysis/{doc_id}/results")
    assert results_res.status_code == 200
    results_data = results_res.json()
    assert results_data["success"] is True
    assert len(results_data["data"]) >= 1


@pytest.mark.asyncio
async def test_orchestrate_case_analysis_endpoint(client: AsyncClient):
    """Test full orchestrator API endpoint /api/v1/analysis/orchestrate."""
    payload = {
        "case_description": "Bị cáo dùng dao khống chế cướp điện thoại di động trị giá 15 triệu đồng",
        "incident_date": "2021-05-10",
        "judgment_date": "2021-08-20",
        "case_id": "api_test_case_001",
        "input_features": {
            "num_facts": 4.0,
            "num_aggravating": 1.0,
            "num_mitigating": 1.0,
            "crime_is_robbery": 1.0,
            "has_dangerous_weapon": 1.0,
        },
    }

    res = await client.post("/api/v1/analysis/orchestrate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "data" in data

    resp_data = data["data"]
    assert resp_data["case_id"] == "api_test_case_001"
    assert "temporal_analysis" in resp_data
    assert resp_data["temporal_analysis"]["document_number"] == "100/2015/QH13"
    assert "predicted_outcome" in resp_data
    assert resp_data["predicted_outcome"]["predicted_outcome"] in ["guilty", "not_guilty"]
    assert "predicted_sentence_years" in resp_data["predicted_outcome"]
    assert resp_data["processing_time_ms"] >= 0


@pytest.mark.asyncio
async def test_auto_split_endpoint(client: AsyncClient):
    """Test auto-split endpoint /api/v1/analysis/auto_split."""
    payload = {
        "text": "- Bị cáo: Trần Văn Nam (SN 1999)\n- Bị hại: Lê Văn Hoàng\n\nKhoảng 20h ngày 12/03/2023, Nam dùng dao đâm Hoàng gây thương tích 25%."
    }
    res = await client.post("/api/v1/analysis/auto_split", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "personal_info" in data["data"]
    assert "case_info" in data["data"]
    assert data["data"]["parties_count"] >= 1


@pytest.mark.asyncio
async def test_web_analyze_endpoint(client: AsyncClient):
    """Test web analyze endpoint /api/v1/analysis/web_analyze."""
    payload = {
        "personal_info": "- Bị cáo: Nguyễn Văn X, chưa có tiền án\n- Bị hại: Trần Y",
        "case_info": "Vào ngày 15/05/2023, bị cáo trộm cắp xe máy 30 triệu đồng, đã trả lại tài sản và thành khẩn khai báo.",
    }
    res = await client.post("/api/v1/analysis/web_analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "parties" in data
    assert "predicted_outcome" in data
    assert "multi_domain" in data
    assert data["multi_domain"]["primary_domain"] == "criminal"
    assert "article_32_penalties" in data
    assert len(data["article_32_penalties"]["principal_penalties"]) == 7
    assert len(data["article_32_penalties"]["supplementary_penalties"]) == 7


@pytest.mark.asyncio
async def test_multi_domain_endpoint(client: AsyncClient):
    """Test multi-domain analysis endpoint /api/v1/analysis/multi_domain."""
    payload = {
        "text": "Công ty X và Công ty Y tranh chấp hợp đồng mua bán trị giá 1 tỷ đồng, yêu cầu phạt vi phạm hợp đồng 10% và giải quyết tại Trọng tài VIAC.",
        "domain": "commercial",
    }
    res = await client.post("/api/v1/analysis/multi_domain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    res_data = data["data"]
    assert res_data["primary_domain"] == "commercial"
    assert "domain_specific_analysis" in res_data
    assert res_data["domain_specific_analysis"]["arbitration_clause_found"] is True

