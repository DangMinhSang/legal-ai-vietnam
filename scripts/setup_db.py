"""
scripts/setup_db.py – Khởi tạo database SQLite cho legal-ai-vietnam.

Chức năng:
1. Tạo thư mục data/db/ nếu chưa tồn tại.
2. Áp dụng tất cả PRAGMA tối ưu hiệu năng (WAL, foreign_keys, cache, …).
3. Tạo toàn bộ bảng ORM (Base.metadata.create_all) nếu chưa có.
4. Tạo FTS5 virtual table fts_text_chunks để full-text search trên text_chunks.
5. Kiểm tra sqlite-vec đã load và in phiên bản.
6. In tóm tắt số bảng đã tồn tại.

Cách dùng:
    # Từ thư mục gốc dự án:
    python scripts/setup_db.py

    # Xem trợ giúp:
    python scripts/setup_db.py --help

    # Chạy với --reset để xoá và tạo lại toàn bộ (NGUY HIỂM - mất dữ liệu):
    python scripts/setup_db.py --reset

Yêu cầu:
    pip install sqlalchemy[asyncio] aiosqlite sqlite-vec
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve project root so that "src.*" imports work regardless of cwd
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import sqlite_vec  # noqa: E402  (must be after sys.path fix)
from sqlalchemy import event, inspect, text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from src.db.models import Base  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("setup_db")

# ---------------------------------------------------------------------------
# Database path
# ---------------------------------------------------------------------------
_DB_DIR = _PROJECT_ROOT / "data" / "db"
_DB_PATH = _DB_DIR / "legal_ai.db"


# ---------------------------------------------------------------------------
# sqlite-vec loader
# ---------------------------------------------------------------------------

def _load_sqlite_vec(dbapi_conn, _record) -> None:
    raw_conn = dbapi_conn
    while hasattr(raw_conn, "_connection"):
        raw_conn = raw_conn._connection
    raw_conn.enable_load_extension(True)
    try:
        sqlite_vec.load(raw_conn)
    finally:
        raw_conn.enable_load_extension(False)


# ---------------------------------------------------------------------------
# DDL for auxiliary virtual tables
# ---------------------------------------------------------------------------

# sqlite-vec virtual table for 768-dim vector embeddings
_VEC_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS vec_text_chunks
USING vec0(
    chunk_id TEXT PRIMARY KEY,
    embedding FLOAT[768]
);
"""

# FTS5 full-text search on text_chunks.content
# Allows queries like: SELECT * FROM fts_text_chunks WHERE fts_text_chunks MATCH 'tội trộm cắp'
_FTS5_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_text_chunks
USING fts5(
    chunk_id UNINDEXED,   -- references text_chunks.id
    content,              -- the searchable text
    tokenize = 'unicode61 remove_diacritics 2'
);
"""

# Trigger: keep fts_text_chunks in sync when text_chunks rows are inserted
_FTS5_INSERT_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS trg_fts_insert
AFTER INSERT ON text_chunks BEGIN
    INSERT INTO fts_text_chunks(chunk_id, content)
    VALUES (NEW.id, NEW.content);
END;
"""

# Trigger: keep fts_text_chunks in sync on update
_FTS5_UPDATE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS trg_fts_update
AFTER UPDATE OF content ON text_chunks BEGIN
    UPDATE fts_text_chunks
    SET content = NEW.content
    WHERE chunk_id = OLD.id;
END;
"""

# Trigger: keep fts_text_chunks in sync on delete
_FTS5_DELETE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS trg_fts_delete
AFTER DELETE ON text_chunks BEGIN
    DELETE FROM fts_text_chunks WHERE chunk_id = OLD.id;
END;
"""

# ---------------------------------------------------------------------------
# Core setup logic
# ---------------------------------------------------------------------------

async def setup(*, reset: bool = False) -> None:
    """Create / reset the database and all required tables."""

    _DB_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Database directory: %s", _DB_DIR)

    db_url = f"sqlite+aiosqlite:///{_DB_PATH}"
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )

    # Load sqlite-vec on every connection
    event.listen(engine.sync_engine, "connect", _load_sqlite_vec)

    async with engine.begin() as conn:

        # ---- Optional: wipe everything first --------------------------------
        if reset:
            log.warning("--reset flag active: dropping all existing tables!")
            await conn.run_sync(Base.metadata.drop_all)
            log.info("All ORM tables dropped.")

        # ---- Essential PRAGMAs ----------------------------------------------
        pragma_map = {
            "journal_mode": "WAL",          # concurrent reads during writes
            "synchronous": "NORMAL",         # good balance safety/speed
            "foreign_keys": "ON",            # enforce FK constraints
            "cache_size": "-65536",          # ~64 MB page cache
            "temp_store": "MEMORY",          # temp tables in RAM
            "mmap_size": "268435456",        # 256 MB memory-mapped I/O
        }
        for pragma, value in pragma_map.items():
            await conn.execute(text(f"PRAGMA {pragma}={value}"))
        log.info("SQLite PRAGMAs applied.")

        # ---- Verify sqlite-vec ----------------------------------------------
        row = await conn.execute(text("SELECT vec_version()"))
        vec_ver = row.scalar()
        log.info("sqlite-vec version: %s", vec_ver)

        # ---- Create ORM tables ----------------------------------------------
        await conn.run_sync(Base.metadata.create_all)
        log.info("ORM tables created (or already exist).")

        # ---- sqlite-vec virtual table ---------------------------------------
        await conn.execute(text(_VEC_DDL.strip()))
        log.info("sqlite-vec virtual table 'vec_text_chunks' ready.")

        # ---- FTS5 virtual table + triggers ----------------------------------
        for ddl in [
            _FTS5_DDL,
            _FTS5_INSERT_TRIGGER,
            _FTS5_UPDATE_TRIGGER,
            _FTS5_DELETE_TRIGGER,
        ]:
            await conn.execute(text(ddl.strip()))
        log.info("FTS5 virtual table 'fts_text_chunks' ready.")

        # ---- Summary --------------------------------------------------------
        def _list_tables(sync_conn):
            return inspect(sync_conn).get_table_names()

        table_names = await conn.run_sync(_list_tables)
        log.info("Tables in database (%d):", len(table_names))
        for name in sorted(table_names):
            log.info("  • %s", name)

    await engine.dispose()
    log.info("Setup complete. Database: %s", _DB_PATH)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialise the legal-ai-vietnam SQLite database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_db.py               # First-time setup or safe re-run
  python scripts/setup_db.py --reset       # Drop everything and recreate (DATA LOSS)
        """,
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        default=False,
        help="DROP all tables before recreating them. DESTRUCTIVE – deletes all data.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    if args.reset:
        confirm = input(
            "\n[WARNING] --reset will DELETE ALL DATA in the database.\n"
            "Type 'yes' to confirm, anything else to abort: "
        ).strip()
        if confirm.lower() != "yes":
            log.info("Aborted.")
            sys.exit(0)

    asyncio.run(setup(reset=args.reset))
