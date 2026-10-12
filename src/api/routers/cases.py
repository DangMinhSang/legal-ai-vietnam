"""Case management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.schemas.common import APIResponse, PaginatedResponse
from src.db.models import Case

router = APIRouter()


class CaseCreateRequest(BaseModel):
    case_code: str = Field(description="Mã vụ án")
    title: str = Field(description="Tiêu đề vụ án")
    legal_domain: str = Field(default="criminal", description="Lĩnh vực pháp lý")
    status: str = Field(default="first_instance", description="Giai đoạn xét xử")


class CaseResponse(BaseModel):
    id: str
    case_code: str | None = None
    title: str | None = None
    legal_domain: str | None = None
    status: str
    created_at: str


@router.get("/", response_model=PaginatedResponse[CaseResponse])
async def list_cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CaseResponse]:
    """List all legal cases with pagination."""
    offset = (page - 1) * page_size
    count_stmt = select(func.count(Case.id))
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = select(Case).order_by(Case.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    cases = result.scalars().all()

    items = [
        CaseResponse(
            id=c.id,
            case_code=c.case_code,
            title=c.title,
            legal_domain=c.legal_domain,
            status=c.status,
            created_at=c.created_at.isoformat() if c.created_at else "",
        )
        for c in cases
    ]

    return PaginatedResponse[CaseResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.get("/{case_id}", response_model=APIResponse[CaseResponse])
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CaseResponse]:
    """Get single case details."""
    stmt = select(Case).where(Case.id == case_id)
    res = await db.execute(stmt)
    c = res.scalar_one_or_none()

    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vụ án với ID: {case_id}",
        )

    return APIResponse[CaseResponse](
        success=True,
        data=CaseResponse(
            id=c.id,
            case_code=c.case_code,
            title=c.title,
            legal_domain=c.legal_domain,
            status=c.status,
            created_at=c.created_at.isoformat() if c.created_at else "",
        ),
        message="Lấy thông tin vụ án thành công",
    )


@router.post("/", response_model=APIResponse[CaseResponse], status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CaseResponse]:
    """Create a new case record."""
    new_case = Case(
        case_code=payload.case_code,
        title=payload.title,
        legal_domain=payload.legal_domain,
        status=payload.status,
    )
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)

    return APIResponse[CaseResponse](
        success=True,
        data=CaseResponse(
            id=new_case.id,
            case_code=new_case.case_code,
            title=new_case.title,
            legal_domain=new_case.legal_domain,
            status=new_case.status,
            created_at=new_case.created_at.isoformat() if new_case.created_at else "",
        ),
        message="Tạo vụ án thành công",
    )
