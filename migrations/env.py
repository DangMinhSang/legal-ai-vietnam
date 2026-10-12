"""
Alembic environment configuration for Legal AI Vietnam.

Supports async SQLite via aiosqlite.
Run migrations:
    alembic upgrade head
    alembic revision --autogenerate -m "description"
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ---------------------------------------------------------------------------
# Alembic Config object (alembic.ini values)
# ---------------------------------------------------------------------------
config = context.config

# Set up loguru-compatible logging (optional: alembic uses stdlib logging)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import project metadata so autogenerate can detect model changes
# ---------------------------------------------------------------------------
# Import Base here once database models are defined, e.g.:
# from src.db.models import Base
# target_metadata = Base.metadata
target_metadata = None  # Replace with Base.metadata when models exist

# ---------------------------------------------------------------------------
# Override sqlalchemy.url from project settings (reads .env)
# ---------------------------------------------------------------------------
def _get_url() -> str:
    """Read database URL from project settings (respects .env file)."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config.settings import get_settings
        return get_settings().db.database_url
    except Exception:
        # Fallback: use alembic.ini value
        return config.get_main_option("sqlalchemy.url", "sqlite+aiosqlite:///./data/db/legal_ai.db")


# ---------------------------------------------------------------------------
# Offline migrations (generate SQL without connecting)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL script)."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (connect to database and apply)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and apply migrations."""
    url = _get_url()

    # Build config dict for async engine
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects and applies immediately)."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
