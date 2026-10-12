"""Database layer: SQLite với sqlite-vec cho vector search.

Cung cấp:
- Async SQLAlchemy engine với aiosqlite
- sqlite-vec extension để lưu và tìm kiếm vector embedding
- ORM models cho toàn bộ schema pháp lý
- Dependency injection cho FastAPI (get_db)
"""

from src.db.database import engine, get_db, init_db
from src.db.models import (
    AppealRecord,
    Base,
    Case,
    CaseFact,
    Document,
    AnalysisResultModel,
    DocumentSource,
    EvaluationResult,
    JudgmentDocument,
    JudgmentOutcome,
    LegalDocument,
    LegalProvision,
    PredictionRun,
    Precedent,
    TextChunk,
)

__all__ = [
    "engine",
    "get_db",
    "init_db",
    "Base",
    "Document",
    "AnalysisResultModel",
    "LegalDocument",
    "LegalProvision",
    "Precedent",
    "JudgmentDocument",
    "Case",
    "CaseFact",
    "JudgmentOutcome",
    "AppealRecord",
    "TextChunk",
    "DocumentSource",
    "PredictionRun",
    "EvaluationResult",
]
