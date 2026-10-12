"""Shared response schemas for Legal AI Vietnam API."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized top-level API response envelope."""

    success: bool = True
    data: T | None = None
    message: str | None = None
    errors: list[str] = Field(default_factory=list)


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list response."""

    items: list[T] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    has_next: bool
