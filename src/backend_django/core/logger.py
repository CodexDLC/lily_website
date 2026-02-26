import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from types import FrameType

# Alias for convenience
log = logger


class InterceptHandler(logging.Handler):
    """
    Intercepts standard `logging` messages and redirects them to `loguru`.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Redirects log record to loguru."""
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = logging.currentframe()
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def setup_logging(base_dir: Path, config: dict[str, Any]) -> None:
    """
    Configures loguru for Django.

    Args:
        base_dir: Root project directory (BASE_DIR).
        config: Dictionary with settings (LOG_LEVEL_CONSOLE, etc.).
    """
    # Remove default loguru handlers
    logger.remove()

    # Define paths
    # In container base_dir = /app. Locally = src/backend_django.
    # Create logs inside base_dir to avoid permission issues in Docker.
    log_dir = base_dir / "logs" / "backend"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_debug = log_dir / "debug.log"
    log_file_errors = log_dir / "errors.json"

    # Logging levels
    console_level = config.get("LOG_LEVEL_CONSOLE", "INFO")
    file_level = config.get("LOG_LEVEL_FILE", "DEBUG")
    rotation = config.get("LOG_ROTATION", "10 MB")
    debug = config.get("DEBUG", False)

    # 1. Console output (Pretty)
    logger.add(
        sink=sys.stdout,
        level=console_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<magenta>Django</magenta> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # 2. Debug file (Detailed)
    logger.add(
        sink=str(log_file_debug),
        level=file_level,
        rotation=rotation,
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,  # Async write
        backtrace=debug,
        diagnose=debug,
    )

    # 3. Errors file (JSON for monitoring)
    logger.add(
        sink=str(log_file_errors),
        level="ERROR",
        serialize=True,
        rotation=rotation,
        compression="zip",
        enqueue=True,
    )

    # 4. Intercept standard logging (Django, Libraries)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Configure levels for noisy libraries
    logging.getLogger("django").setLevel(logging.INFO)
    logging.getLogger("django.db.backends").setLevel(logging.WARNING)
    logging.getLogger("django.utils.autoreload").setLevel(logging.WARNING)

    if not debug:
        logging.getLogger("django.request").setLevel(logging.ERROR)

    logger.info(f"Loguru setup complete. Logs directory: {log_dir}")
