"""Async database engine và session factory dùng SQLite + sqlite-vec.

Kiến trúc:
- SQLAlchemy 2.0 async engine với aiosqlite dialect
- sqlite-vec extension nạp tự động khi mở connection (qua event listener)
- AsyncSession factory cho dependency injection FastAPI
- init_db() tạo toàn bộ bảng khi khởi động lần đầu
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

import sqlite_vec
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event, text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database file path
# ---------------------------------------------------------------------------
_DB_DIR = Path(__file__).resolve().parents[2] / "data" / "db"
_DB_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _DB_DIR / "legal_ai.db"

DATABASE_URL = f"sqlite+aiosqlite:///{_DB_PATH}"

# ---------------------------------------------------------------------------
# Async engine
# ---------------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # Set True to log all SQL (very verbose)
    future=True,
    connect_args={
        # Allow reading from multiple threads (safe for read-only ops)
        "check_same_thread": False,
        # WAL mode: concurrent reads while writing
        "timeout": 30,
    },
)


# ---------------------------------------------------------------------------
# Load sqlite-vec extension on every new connection
# ---------------------------------------------------------------------------
@event.listens_for(engine.sync_engine, "connect")
def _load_sqlite_vec(dbapi_connection, connection_record):  # noqa: ARG001
    """Enable and load the sqlite-vec extension for vector operations."""
    raw_conn = dbapi_connection
    while hasattr(raw_conn, "_connection"):
        raw_conn = raw_conn._connection
    raw_conn.enable_load_extension(True)
    try:
        sqlite_vec.load(raw_conn)
        logger.debug("sqlite-vec extension loaded successfully.")
    except Exception as exc:
        logger.error("Failed to load sqlite-vec extension: %s", exc)
        raise
    finally:
        raw_conn.enable_load_extension(False)


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session; roll back on exception, close always.

    Usage in FastAPI::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------
async def init_db() -> None:
    """Create all tables defined in models.py if they do not already exist.

    Also runs essential SQLite PRAGMA settings for performance and integrity,
    and verifies that sqlite-vec is operational.
    """
    from src.db.models import Base  # local import to avoid circular deps

    async with engine.begin() as conn:
        # Performance and durability PRAGMAs
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.execute(text("PRAGMA cache_size=-64000"))   # ~64 MB cache
        await conn.execute(text("PRAGMA temp_store=MEMORY"))

        # Verify sqlite-vec is loaded
        result = await conn.execute(text("SELECT vec_version()"))
        version = result.scalar()
        logger.info("sqlite-vec version: %s", version)

        # Create all ORM tables
        await conn.run_sync(Base.metadata.create_all)

        # Create sqlite-vec virtual table
        await conn.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS vec_text_chunks "
                "USING vec0(chunk_id TEXT PRIMARY KEY, embedding FLOAT[768])"
            )
        )

        # Create FTS5 virtual table and triggers
        await conn.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS fts_text_chunks "
                "USING fts5(chunk_id UNINDEXED, content, tokenize = 'unicode61 remove_diacritics 2')"
            )
        )
        logger.info("Database initialised at: %s", _DB_PATH)


async def close_db() -> None:
    """Dispose the engine connection pool (call on application shutdown)."""
    await engine.dispose()
    logger.info("Database engine disposed.")
