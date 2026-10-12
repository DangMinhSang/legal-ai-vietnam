"""
Logging configuration for Legal AI Vietnam.

Sets up Loguru with:
- Coloured console output (development)
- Rotating file handler (production)
- Interception of stdlib logging (for third-party libraries)

Usage:
    from config.logging_config import setup_logging
    setup_logging()  # Call once at application startup
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

# ============================================================
# Log formats
# ============================================================

# Development: human-readable with colour
DEV_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Production / file: machine-parseable (no ANSI codes)
FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{name}:{function}:{line} - "
    "{message}"
)

# Minimal format for test output
TEST_FORMAT = "<level>{level: <8}</level> | {name}:{line} - <level>{message}</level>"


# ============================================================
# stdlib logging interception
# ============================================================


class _InterceptHandler(logging.Handler):
    """
    Route all stdlib logging calls through Loguru.

    This captures log messages from third-party libraries
    (SQLAlchemy, httpx, uvicorn, etc.) so they appear in the
    same stream as our application logs.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Find caller depth so Loguru reports the correct origin
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _intercept_stdlib_logging(level: str = "INFO") -> None:
    """Redirect all stdlib loggers through Loguru."""
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # Silence noisy third-party loggers
    for noisy in (
        "httpx",
        "httpcore",
        "urllib3",
        "multipart",
        "aiosqlite",
        "fastembed",
        "huggingface_hub",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ============================================================
# Public API
# ============================================================


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    rotation: str = "10 MB",
    retention: str = "30 days",
    dev_mode: bool = False,
    test_mode: bool = False,
) -> None:
    """
    Configure Loguru for the application.

    Args:
        level: Minimum log level (DEBUG / INFO / WARNING / ERROR / CRITICAL).
        log_file: Path to the rotating log file. Defaults to logs/legal_ai.log.
        rotation: Loguru rotation trigger (e.g. "10 MB", "1 day").
        retention: How long to keep old log files (e.g. "30 days").
        dev_mode: If True, use verbose coloured format for console.
        test_mode: If True, use minimal format (no file handler).
    """
    # Remove default Loguru handler
    logger.remove()

    # ---- Console handler ----
    console_format = DEV_FORMAT if (dev_mode or test_mode) else DEV_FORMAT
    logger.add(
        sys.stderr,
        format=console_format,
        level=level,
        colorize=True,
        backtrace=dev_mode,
        diagnose=dev_mode,
    )

    # ---- File handler (skip in test mode) ----
    if not test_mode:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        target = log_file or LOG_DIR / "legal_ai.log"
        logger.add(
            str(target),
            format=FILE_FORMAT,
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=False,  # Keep diagnose=False in files (sensitive data)
            enqueue=True,    # Thread-safe async logging
        )

    # ---- Intercept stdlib logging ----
    _intercept_stdlib_logging(level)

    logger.debug(
        "Logging configured | level={} dev_mode={} test_mode={}",
        level,
        dev_mode,
        test_mode,
    )


def get_logger(name: str):
    """
    Return a Loguru logger bound with a module name context.

    Usage:
        from config.logging_config import get_logger
        log = get_logger(__name__)
        log.info("Module started")

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A Loguru logger with the name bound.
    """
    return logger.bind(name=name)


def setup_from_settings() -> None:
    """
    Convenience: read settings and call setup_logging().

    Call this in the application entry-point (main.py / cli.py)
    after the Settings object is initialised.
    """
    from config.settings import get_settings

    s = get_settings()
    setup_logging(
        level=s.app.log_level,
        dev_mode=s.app.debug,
    )
