"""Pytest fixtures and test configuration for Legal AI Vietnam.

Fixtures include:
- anyio_backend: enforces asyncio
- test_db: fresh in-memory SQLite session with sqlite-vec and all tables
- client: httpx AsyncClient hooked to FastAPI app with DB dependency override
- sample_judgment_text: synthetic sample judgment marked for non-production use
- sample_legal_text: synthetic law text marked for non-production use
- Legacy fixtures: sample_legal_document, sample_case, sample_precedent, sample_judgment
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import pytest
import pytest_asyncio
import sqlite_vec
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.api.deps import _MockEmbeddingService, get_db, get_embedding_service
import src.api.deps as api_deps
from src.api.main import app
from src.db.models import (
    Base,
    Case,
    CaseFact,
    Document,
    JudgmentDocument,
    JudgmentOutcome,
    LegalDocument,
    LegalProvision,
    Precedent,
    TextChunk,
)


@pytest.fixture(scope="session")
def anyio_backend():
    """Specify backend for anyio."""
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Event loop policy for pytest-asyncio."""
    return asyncio.DefaultEventLoopPolicy()


# ---------------------------------------------------------------------------
# Test database fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """In-memory SQLite database session for tests with sqlite-vec loaded."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _load_vec(dbapi_conn, _rec):
        raw_conn = dbapi_conn
        while hasattr(raw_conn, "_connection"):
            raw_conn = raw_conn._connection
        raw_conn.enable_load_extension(True)
        try:
            sqlite_vec.load(raw_conn)
        except Exception:
            pass
        finally:
            raw_conn.enable_load_extension(False)

    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(
                text(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS vec_text_chunks "
                    "USING vec0(chunk_id TEXT PRIMARY KEY, embedding FLOAT[768])"
                )
            )
        except Exception:
            pass

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client configured with test database session override."""
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    mock_emb = _MockEmbeddingService()
    api_deps._embedding_service_instance = mock_emb
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_emb

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample text fixtures (synthetic test data)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_judgment_text() -> str:
    """Bản án mẫu được đánh dấu rõ là DỮ LIỆU GIẢ LẬP - KHÔNG dùng cho đánh giá."""
    return """
    [SAMPLE DATA - NOT REAL JUDGMENT]
    BẢN ÁN SỐ: 01/2023/HSST
    TAND Quận 1, TP.HCM
    Ngày xét xử: 15/01/2023

    BỊ CÁO: Nguyễn Văn A (tên giả lập)
    Sinh năm: 1990

    TỘI DANH: Tội trộm cắp tài sản
    ĐIỀU KHOẢN: Điều 173 khoản 1 BLHS 2015

    HÌNH PHẠT: 1 năm 6 tháng tù giam
    [END SAMPLE DATA]
    """


@pytest.fixture
def sample_legal_text() -> str:
    """Điều luật mẫu - DỮ LIỆU GIẢ LẬP."""
    return """
    [SAMPLE DATA - NOT REAL LAW]
    Điều 173. Tội trộm cắp tài sản
    1. Người nào trộm cắp tài sản của người khác...
    [END SAMPLE DATA]
    """


# ---------------------------------------------------------------------------
# Additional compatibility fixtures for existing unit tests
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session(test_db: AsyncSession) -> AsyncSession:
    """Alias for test_db for backward compatibility."""
    return test_db


@pytest_asyncio.fixture
async def sample_legal_document(test_db: AsyncSession) -> LegalDocument:
    """LegalDocument fixture."""
    doc = LegalDocument(
        doc_type="law",
        doc_number="15/2022/QH15",
        title="Luật Kinh doanh bảo hiểm",
        issuing_body="Quốc hội",
        signing_date=datetime(2022, 6, 16),
        effective_date=datetime(2023, 1, 1),
        status="active",
        source_url="https://vbpl.vn/sample",
        full_text="Điều 1. Phạm vi điều chỉnh...",
        meta={"domain": "insurance"},
    )
    test_db.add(doc)
    await test_db.flush()
    return doc


@pytest_asyncio.fixture
async def sample_case(test_db: AsyncSession) -> Case:
    """Case fixture."""
    case = Case(
        case_code="HS-2023-001",
        title="Nguyễn Văn A về tội trộm cắp tài sản",
        legal_domain="criminal",
        status="first_instance",
        incident_date=datetime(2023, 3, 15),
    )
    test_db.add(case)
    await test_db.flush()
    return case


@pytest_asyncio.fixture
async def sample_judgment(test_db: AsyncSession) -> JudgmentDocument:
    """JudgmentDocument fixture."""
    judgment = JudgmentDocument(
        judgment_number="15/2023/HSST",
        judgment_type="first_instance",
        legal_domain="criminal",
        court_name="Tòa án nhân dân quận 1, TP.HCM",
        court_level="district",
        judgment_date=datetime(2023, 8, 20),
        full_text="NHÂN DANH NƯỚC CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM...",
    )
    test_db.add(judgment)
    await test_db.flush()
    return judgment


@pytest_asyncio.fixture
async def sample_precedent(test_db: AsyncSession) -> Precedent:
    """Precedent fixture for testing."""
    precedent = Precedent(
        precedent_number="01/2016/AL",
        title="Án lệ số 01/2016/AL về vụ án Giết người",
        legal_issue_summary="Tình huống án lệ về hành vi dùng hung khí nguy hiểm",
        legal_solution="Khái quát nội dung giải pháp pháp lý",
        full_text="Nội dung toàn văn án lệ...",
        legal_domain="criminal",
        publication_date=datetime(2016, 4, 6),
    )
    test_db.add(precedent)
    await test_db.flush()
    return precedent
