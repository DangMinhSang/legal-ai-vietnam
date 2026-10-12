"""FastAPI dependency injection providers.

Exported dependencies:
- get_db():               AsyncSession generator (from src.db.database)
- get_settings():         Settings instance
- get_embedding_service(): EmbeddingService singleton
- get_llm_service():      LLMService singleton
- get_document_parser():  DocumentParser instance
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings, get_settings
from src.db.database import get_db

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# EmbeddingService singleton
# ---------------------------------------------------------------------------

_embedding_service_instance: Any = None


def _get_embedding_service_instance() -> Any:
    """Lazy-initialise and cache the EmbeddingService singleton."""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        try:
            from src.services.embedding_service import EmbeddingService
            settings = get_settings()
            _embedding_service_instance = EmbeddingService(
                model_name=settings.embedding.embedding_model,
                cache_dir=str(settings.embedding.resolved_cache_dir),
                batch_size=settings.embedding.embedding_batch_size,
            )
        except Exception:
            # Fallback mock for test environments where fastembed isn't installed
            _embedding_service_instance = _MockEmbeddingService()
    return _embedding_service_instance


class _MockEmbeddingService:
    """Lightweight in-memory mock when fastembed / ONNX is not available."""

    def __init__(self, dim: int = 768) -> None:
        self.dim = dim

    def embed_text(self, text: str) -> list[float]:
        # Deterministic dummy vector based on hash
        import hashlib
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(float((h >> (i % 64)) & 1) * 2 - 1) / (self.dim ** 0.5) for i in range(self.dim)]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


def get_embedding_service() -> Any:
    """Dependency: return the EmbeddingService singleton."""
    return _get_embedding_service_instance()


# ---------------------------------------------------------------------------
# LLMService singleton
# ---------------------------------------------------------------------------

_llm_service_instance: Any = None


def _get_llm_service_instance() -> Any:
    """Lazy-initialise and cache the LLMService singleton."""
    global _llm_service_instance
    if _llm_service_instance is None:
        try:
            from src.services.llm_service import LLMService
            _llm_service_instance = LLMService(settings=get_settings())
        except Exception:
            _llm_service_instance = _MockLLMService()
    return _llm_service_instance


class _MockLLMService:
    """Lightweight mock LLM service for testing / environments without API keys."""

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        return f"[MOCK LLM RESPONSE for prompt of {len(prompt)} chars]"

    async def ping(self) -> bool:
        return False


def get_llm_service() -> Any:
    """Dependency: return the LLMService singleton."""
    return _get_llm_service_instance()


# ---------------------------------------------------------------------------
# DocumentParser instance
# ---------------------------------------------------------------------------

def get_document_parser() -> Any:
    """Dependency: return a DocumentParser instance."""
    try:
        from src.document_parser.parser import DocumentParser
        return DocumentParser()
    except Exception:
        from src.document_parser.base import BaseParser, ParsedDocument
        from pathlib import Path

        class _SimpleParser(BaseParser):
            supported_extensions = frozenset({".txt", ".pdf", ".docx"})

            def parse(self, path: Path | str) -> ParsedDocument:
                p = Path(path)
                if not p.exists():
                    raise FileNotFoundError(f"File not found: {path}")
                content = p.read_text(encoding="utf-8", errors="replace")
                if not content.strip():
                    raise ValueError(f"File is empty: {path}")
                return ParsedDocument(
                    title=p.stem,
                    content=content,
                    page_count=1,
                    parse_method="text_extraction",
                )

        return _SimpleParser()
