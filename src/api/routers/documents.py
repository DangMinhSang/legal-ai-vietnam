"""Document management endpoints."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_document_parser, get_embedding_service
from src.api.schemas.common import APIResponse, PaginatedResponse
from src.api.schemas.document import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentUploadResponse,
)
from src.db.database import AsyncSessionLocal
from src.db.models import Document, TextChunk
from src.document_parser.base import BaseParser

router = APIRouter()


# ---------------------------------------------------------------------------
# Background task for chunking and embeddings
# ---------------------------------------------------------------------------

async def _chunk_and_embed_document(document_id: str, content: str) -> None:
    """Background task: chunk text and compute embeddings without blocking response."""
    if not content.strip():
        return

    logger.info("Starting background embedding generation for document {}", document_id)
    try:
        # Simple paragraph / fixed-size chunking
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunks_text: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for p in paragraphs:
            if current_len + len(p) > 1000 and current_chunk:
                chunks_text.append("\n\n".join(current_chunk))
                current_chunk = [p]
                current_len = len(p)
            else:
                current_chunk.append(p)
                current_len += len(p)
        if current_chunk:
            chunks_text.append("\n\n".join(current_chunk))

        if not chunks_text:
            chunks_text = [content[:1000]]

        # Obtain embedding service
        from src.api.deps import _get_embedding_service_instance
        emb_service = _get_embedding_service_instance()

        vectors = []
        if emb_service is not None and hasattr(emb_service, "embed_batch"):
            try:
                vectors = emb_service.embed_batch(chunks_text)
            except Exception as e:
                logger.warning("Embedding generation warning: {}", e)

        # Write chunks to DB
        async with AsyncSessionLocal() as session:
            for idx, chunk_str in enumerate(chunks_text):
                vec = vectors[idx] if idx < len(vectors) else None
                chunk_record = TextChunk(
                    content=chunk_str,
                    chunk_index=idx,
                    token_count=len(chunk_str.split()),
                    embedding_model="fastembed" if vec else None,
                    embedding=vec,
                    embedding_dim=len(vec) if vec else None,
                    meta={"document_id": document_id},
                )
                session.add(chunk_record)

            # Update document status to ready
            stmt = select(Document).where(Document.id == document_id)
            res = await session.execute(stmt)
            doc = res.scalar_one_or_none()
            if doc:
                doc.status = "ready"

            await session.commit()
            logger.info("Completed embedding generation for document {}: {} chunks created", document_id, len(chunks_text))
    except Exception as exc:
        logger.error("Failed to generate embeddings for document {}: {}", document_id, exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    parser: BaseParser = Depends(get_document_parser),
) -> DocumentUploadResponse:
    """Upload legal document (PDF, DOCX, TXT), parse text, and trigger async embeddings."""
    filename = file.filename or "unknown.txt"
    suffix = Path(filename).suffix.lower()

    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng tệp không được hỗ trợ: '{suffix}'. Chỉ chấp nhận .pdf, .docx, .txt",
        )

    # Save to temporary file for parser
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
        content = await file.read()
        tmp.write(content)

    try:
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp rỗng (0 bytes)",
            )

        parsed = parser.parse(tmp_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Lỗi khi đọc tài liệu: {exc}",
        )
    finally:
        if tmp_path.exists():
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    # Save to database
    doc = Document(
        filename=filename,
        file_type=suffix.lstrip("."),
        status="uploaded",
        page_count=parsed.page_count,
        extracted_text=parsed.content,
        extracted_text_length=len(parsed.content),
        parse_method=parsed.parse_method,
        warnings=parsed.warnings,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Trigger background chunking and embedding
    background_tasks.add_task(_chunk_and_embed_document, doc.id, parsed.content)

    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
        page_count=doc.page_count,
        extracted_text_length=doc.extracted_text_length,
        parse_method=doc.parse_method,
        warnings=doc.warnings or [],
    )


@router.get("/", response_model=PaginatedResponse[DocumentListItem])
async def list_documents(
    page: int = Query(default=1, ge=1, description="Số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số phần tử mỗi trang"),
    status_filter: str | None = Query(default=None, alias="status", description="Lọc theo trạng thái"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DocumentListItem]:
    """List documents with pagination and optional status filter."""
    offset = (page - 1) * page_size

    # Base query excluding soft-deleted documents
    query = select(Document).where(Document.status != "deleted")
    count_query = select(func.count(Document.id)).where(Document.status != "deleted")

    if status_filter:
        query = query.where(Document.status == status_filter)
        count_query = count_query.where(Document.status == status_filter)

    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    query = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    docs = result.scalars().all()

    items = [
        DocumentListItem(
            id=d.id,
            filename=d.filename,
            processing_status=d.status,
            page_count=d.page_count,
            linked_case_id=d.linked_case_id,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in docs
    ]

    return PaginatedResponse[DocumentListItem](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.get("/{document_id}", response_model=APIResponse[DocumentDetailResponse])
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DocumentDetailResponse]:
    """Get full document details including extracted text."""
    stmt = select(Document).where(Document.id == document_id, Document.status != "deleted")
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tài liệu với ID '{document_id}' không tồn tại hoặc đã bị xoá",
        )

    data = DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        processing_status=doc.status,
        page_count=doc.page_count,
        extracted_text=doc.extracted_text,
        extracted_text_length=doc.extracted_text_length,
        parse_method=doc.parse_method,
        warnings=doc.warnings or [],
        linked_case_id=doc.linked_case_id,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
    )

    return APIResponse[DocumentDetailResponse](
        success=True,
        data=data,
        message="Lấy thông tin tài liệu thành công",
    )


@router.delete("/{document_id}", response_model=APIResponse[dict[str, str]])
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict[str, str]]:
    """Soft delete document by setting status to 'deleted'."""
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc or doc.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tài liệu với ID '{document_id}' không tồn tại",
        )

    doc.status = "deleted"
    await db.commit()

    return APIResponse[dict[str, str]](
        success=True,
        data={"id": document_id, "status": "deleted"},
        message="Đã xoá tài liệu thành công",
    )
