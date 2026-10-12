"""
Script khởi tạo database cho Legal AI Vietnam.

Tạo tất cả bảng cần thiết trong SQLite.

Cách dùng:
    python scripts/init_db.py

Hoặc nếu dùng Alembic:
    alembic upgrade head
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Thêm project root vào sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


async def init_database() -> None:
    """Tạo database và tất cả bảng."""
    from config.settings import get_settings
    from config.logging_config import setup_from_settings

    setup_from_settings()

    from loguru import logger

    settings = get_settings()

    # Tạo thư mục chứa DB nếu chưa có
    db_path = settings.db.resolved_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Khởi tạo database tại: {}", db_path)

    # TODO: Import và tạo tất cả bảng khi models được định nghĩa
    # from src.db.models import Base
    # from sqlalchemy.ext.asyncio import create_async_engine
    # engine = create_async_engine(settings.db.database_url, echo=True)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    # await engine.dispose()

    logger.info("Database sẵn sàng tại: {}", db_path)
    logger.warning(
        "Lưu ý: Database models chưa được định nghĩa. "
        "Tạo src/db/models.py trước, sau đó chạy: alembic upgrade head"
    )


def main() -> None:
    asyncio.run(init_database())


if __name__ == "__main__":
    main()
