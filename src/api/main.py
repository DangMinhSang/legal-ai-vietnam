"""FastAPI main application entrypoint cho Legal AI Vietnam.

FastAPI app factory với:
- Lifespan context manager: khởi tạo DB, load embedding model, log startup info, close_db khi tắt
- CORS middleware (từ config)
- Logging middleware: log mỗi request với method, path, status, duration
- Include routers: /health, /api/v1/documents, /api/v1/cases, /api/v1/analysis
- Custom exception handlers: HTTPException, ValueError, generic Exception
- OpenAPI metadata tiếng Việt
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from config.settings import get_settings
from src.db.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN001
    """Lifespan context manager: startup and shutdown."""
    settings = get_settings()

    # Startup
    logger.info("Initializing Legal AI Vietnam v{}", settings.app.app_version)
    settings.ensure_directories()
    try:
        await init_db()
        logger.info("Database initialised successfully")
    except Exception as exc:
        logger.error("Database initialisation failed: {}", exc)

    # Try warm-up embedding model
    try:
        from src.api.deps import _get_embedding_service_instance
        _get_embedding_service_instance()
        logger.info("Embedding model loaded")
    except Exception as exc:
        logger.warning("Embedding model warm-up skipped: {}", exc)

    yield

    # Shutdown
    logger.info("Shutting down Legal AI Vietnam...")
    try:
        await close_db()
    except Exception as exc:
        logger.warning("Error during close_db: {}", exc)
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """FastAPI app factory."""
    settings = get_settings()

    app = FastAPI(
        title="Legal AI Vietnam",
        description="Hệ thống AI phân tích và hỗ trợ nghiên cứu án hình sự Việt Nam",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "health", "description": "Kiểm tra tình trạng hệ thống"},
            {"name": "documents", "description": "Quản lý và tải lên tài liệu pháp lý"},
            {"name": "cases", "description": "Quản lý thông tin hồ sơ vụ án"},
            {"name": "analysis", "description": "Phân tích AI và trích xuất tình tiết pháp lý"},
        ],
    )

    # CORS middleware (từ config)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware: log mỗi request với method, path, status, duration
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Any) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "{method} {path} - {status} ({ms:.1f}ms)",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=duration_ms,
        )
        return response

    # Custom exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "message": exc.detail,
                "errors": [str(exc.detail)],
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        logger.warning("ValueError at {}: {}", request.url.path, exc)
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": None,
                "message": "Dữ liệu đầu vào không hợp lệ",
                "errors": [str(exc)],
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception at {}: {}", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "message": "Lỗi nội bộ hệ thống",
                "errors": ["Internal server error"],
            },
        )

    # Include routers
    from src.api.routers import analysis, cases, documents, health

    app.include_router(health.router, tags=["health"])
    app.include_router(
        documents.router,
        prefix="/api/v1/documents",
        tags=["documents"],
    )
    app.include_router(
        cases.router,
        prefix="/api/v1/cases",
        tags=["cases"],
    )
    app.include_router(
        analysis.router,
        prefix="/api/v1/analysis",
        tags=["analysis"],
    )

    # Giao diện Web Demo trực quan với chính xác 2 khung nhập liệu
    from fastapi.responses import HTMLResponse
    from pathlib import Path

    templates_dir = Path(__file__).resolve().parents[2] / "templates"
    index_html_file = templates_dir / "index.html"

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
    async def serve_demo_ui() -> HTMLResponse:
        """Phục vụ giao diện Web Demo cho người dùng."""
        if index_html_file.exists():
            return HTMLResponse(content=index_html_file.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Legal AI Vietnam - Web Demo</h1>")

    return app



app = create_app()
