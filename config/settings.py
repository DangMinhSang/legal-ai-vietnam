"""
Settings module for Legal AI Vietnam.

Reads configuration from environment variables and .env file.
Uses Pydantic BaseSettings for validation and type coercion.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================
# Sub-settings groups
# ============================================================


class DatabaseSettings(BaseSettings):
    """SQLite database configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/db/legal_ai.db",
        description="Async SQLAlchemy database URL",
    )
    db_path: str = Field(
        default="./data/db/legal_ai.db",
        description="Path to the SQLite database file",
    )

    @property
    def resolved_db_path(self) -> Path:
        """Return absolute path to the database file."""
        p = Path(self.db_path)
        if not p.is_absolute():
            return PROJECT_ROOT / p
        return p


class LLMSettings(BaseSettings):
    """LLM / AI model configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")

    llm_primary_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Primary LLM model identifier (LiteLLM format)",
    )
    llm_fallback_model: str = Field(
        default="gpt-4o-mini",
        description="Fallback LLM model when primary is unavailable",
    )
    llm_max_tokens: int = Field(
        default=4096,
        ge=256,
        le=32768,
        description="Maximum tokens per LLM response",
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0.0 = deterministic)",
    )
    llm_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for failed LLM calls",
    )
    llm_retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        description="Base delay in seconds between retries (exponential backoff)",
    )

    @field_validator("anthropic_api_key", "openai_api_key", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Optional[str]) -> Optional[str]:
        """Convert empty strings to None for optional API keys."""
        if v == "" or v == "your_anthropic_api_key_here" or v == "your_openai_api_key_here":
            return None
        return v

    @property
    def has_anthropic(self) -> bool:
        return self.anthropic_api_key is not None

    @property
    def has_openai(self) -> bool:
        return self.openai_api_key is not None

    @property
    def has_any_llm(self) -> bool:
        return self.has_anthropic or self.has_openai


class EmbeddingSettings(BaseSettings):
    """Text embedding model configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    embedding_model: str = Field(
        default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        description="fastembed model name for text embeddings",
    )
    embedding_dim: int = Field(
        default=768,
        ge=64,
        le=4096,
        description="Embedding vector dimension",
    )
    fastembed_cache_dir: str = Field(
        default="./data/models/fastembed",
        description="Local cache directory for downloaded fastembed models",
    )
    embedding_batch_size: int = Field(
        default=32,
        ge=1,
        le=512,
        description="Batch size for embedding generation",
    )
    embedding_max_length: int = Field(
        default=512,
        ge=64,
        le=8192,
        description="Maximum token length for embedding input",
    )

    @property
    def resolved_cache_dir(self) -> Path:
        p = Path(self.fastembed_cache_dir)
        if not p.is_absolute():
            return PROJECT_ROOT / p
        return p


class AppSettings(BaseSettings):
    """Core application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Legal AI Vietnam")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    secret_key: str = Field(
        default="change-this-to-a-random-secret-key",
        description="Secret key for session management. Change before production!",
    )

    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000, ge=1, le=65535)

    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}, got '{v}'")
        return upper


class DataSettings(BaseSettings):
    """Data directory configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    data_raw_dir: str = Field(default="./data/raw")
    data_processed_dir: str = Field(default="./data/processed")
    data_sample_dir: str = Field(default="./data/sample")
    models_dir: str = Field(default="./data/models")

    huggingface_token: Optional[str] = Field(
        default=None,
        description="HuggingFace token for private datasets / higher rate limits",
    )
    random_seed: int = Field(default=42, description="Random seed for reproducibility")
    experiment_name: str = Field(default="legal-ai-vietnam-mvp")

    @field_validator("huggingface_token", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Optional[str]) -> Optional[str]:
        return None if not v else v

    def _resolve(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def raw_dir(self) -> Path:
        return self._resolve(self.data_raw_dir)

    @property
    def processed_dir(self) -> Path:
        return self._resolve(self.data_processed_dir)

    @property
    def sample_dir(self) -> Path:
        return self._resolve(self.data_sample_dir)

    @property
    def resolved_models_dir(self) -> Path:
        return self._resolve(self.models_dir)


class CrawlerSettings(BaseSettings):
    """Web crawler / scraper configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    crawler_delay_seconds: float = Field(
        default=2.0,
        ge=0.5,
        description="Minimum delay between HTTP requests (rate limiting)",
    )
    crawler_max_concurrent: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of concurrent HTTP requests",
    )
    crawler_user_agent: str = Field(
        default="LegalAIResearch/0.1 (academic research; contact: research@example.com)",
        description="HTTP User-Agent string for crawlers",
    )


class EvaluationSettings(BaseSettings):
    """Evaluation and experiment tracking configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    random_seed: int = Field(default=42)
    # Temporal split: judgments BEFORE this date go to train set
    # Prevents data leakage (future judgments influencing past predictions)
    temporal_split_date: str = Field(
        default="2022-01-01",
        description="ISO date string. Judgments before this go to train, after to test.",
    )
    min_samples_per_class: int = Field(
        default=10,
        ge=1,
        description="Minimum samples per class for valid training",
    )

    @field_validator("temporal_split_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"temporal_split_date must be YYYY-MM-DD format, got '{v}'")
        return v


# ============================================================
# Composite Settings
# ============================================================


class Settings(BaseSettings):
    """
    Master settings object that composes all sub-settings.

    Usage:
        from config.settings import get_settings
        settings = get_settings()
        print(settings.llm.primary_model)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Sub-settings are instantiated as nested models
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    crawler: CrawlerSettings = Field(default_factory=CrawlerSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    def ensure_directories(self) -> None:
        """Create all required data directories if they don't exist."""
        dirs = [
            self.data.raw_dir,
            self.data.processed_dir,
            self.data.sample_dir,
            self.data.resolved_models_dir,
            self.db.resolved_db_path.parent,
            self.embedding.resolved_cache_dir,
            PROJECT_ROOT / "logs",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def validate_for_production(self) -> list[str]:
        """
        Run pre-flight checks. Returns a list of warning strings.
        Call this at startup to catch misconfigurations early.
        """
        warnings: list[str] = []

        if not self.llm.has_any_llm:
            warnings.append(
                "No LLM API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )
        if self.app.secret_key == "change-this-to-a-random-secret-key":
            warnings.append(
                "SECRET_KEY is using the default value. "
                "Generate a secure key: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if self.app.debug and not os.getenv("CI"):
            warnings.append("DEBUG=true in what looks like a production environment.")

        return warnings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    The lru_cache ensures settings are only parsed once per process.
    In tests, call get_settings.cache_clear() before patching env vars.

    Returns:
        Settings: Fully validated application settings.
    """
    return Settings()
