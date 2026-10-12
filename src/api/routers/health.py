"""Health check and diagnostic endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from src.api.deps import get_db, get_embedding_service, get_llm_service

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness probe."""
    settings = get_settings()
    return {"status": "ok", "version": settings.app.app_version}


@router.get("/health/detailed")
async def detailed_health(
    db: AsyncSession = Depends(get_db),
    embedding_service: object = Depends(get_embedding_service),
    llm_service: object = Depends(get_llm_service),
) -> dict[str, str]:
    """Detailed health check for database, embedding service, and LLM connection."""
    # 1. Database check
    db_status = "connected"
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() != 1:
            db_status = "unhealthy"
    except Exception:
        db_status = "disconnected"

    # 2. Embedding model check
    emb_status = "loaded" if embedding_service is not None else "not_loaded"

    # 3. LLM API ping check
    llm_status = "unreachable"
    if llm_service is not None and hasattr(llm_service, "ping"):
        try:
            is_ok = await llm_service.ping()
            llm_status = "reachable" if is_ok else "unreachable"
        except Exception:
            llm_status = "unreachable"
    elif llm_service is not None:
        llm_status = "reachable"

    overall = "ok" if db_status == "connected" else "degraded"

    return {
        "status": overall,
        "database": db_status,
        "embedding_model": emb_status,
        "llm_api": llm_status,
    }
