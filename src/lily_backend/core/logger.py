import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Union

from django.conf import settings

if TYPE_CHECKING:
    from loguru import Logger

# Declare logger with a Union type to satisfy mypy
logger: Union[logging.Logger, "Logger"]

try:
    from codex_core.common.loguru_setup import setup_logging
    from loguru import logger as loguru_logger

    logger = loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    LOGURU_AVAILABLE = False


class DjangoLoggingSettingsAdapter:
    """Adapts Django settings to codex-core LoggingSettingsProtocol."""

    def __init__(self) -> None:
        self.log_level_console = getattr(settings, "LOG_LEVEL_CONSOLE", "INFO")
        self.log_level_file = getattr(settings, "LOG_LEVEL_FILE", "DEBUG")
        self.log_rotation = getattr(settings, "LOG_ROTATION", "10 MB")
        self.log_dir = getattr(settings, "LOG_DIR", "logs")
        self.debug = getattr(settings, "DEBUG", False)


class InterceptHandler(logging.Handler):
    """Redirect standard logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        if isinstance(logger, logging.Logger):
            logger.handle(record)
            return

        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _setup_windows_logging(adapter: DjangoLoggingSettingsAdapter, service_name: str) -> None:
    """
    Configure loguru without file rotation on Windows.

    Rotating a shared `debug.log` via rename() is unreliable on Windows when the
    Django autoreloader or another process keeps the file handle open.
    """
    if isinstance(logger, logging.Logger):
        return

    base_log_dir = Path(adapter.log_dir) / service_name
    base_log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sink=sys.stdout,
        level=adapter.log_level_console.upper(),
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            f"<magenta>{service_name}</magenta> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )
    logger.add(
        sink=str(base_log_dir / "debug.log"),
        level=adapter.log_level_file.upper(),
        format="{time} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
        backtrace=adapter.debug,
        diagnose=adapter.debug,
    )
    logger.add(
        sink=str(base_log_dir / "errors.json"),
        level="ERROR",
        serialize=True,
        enqueue=True,
        backtrace=adapter.debug,
        diagnose=adapter.debug,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("django", "django.server", "django.db.backends"):
        logging.getLogger(name).handlers = [InterceptHandler()]

    logging.getLogger("django.db.backends").setLevel(logging.WARNING)
    logging.getLogger("django.utils.autoreload").setLevel(logging.WARNING)
    logging.getLogger("django_lifecycle").setLevel(logging.WARNING)

    logger.info(
        "Loguru initialized in Windows-safe mode for {}. Logs: {}",
        service_name,
        base_log_dir,
    )


def init_logging() -> None:
    """Initialize logging based on project settings and available libraries."""
    if not LOGURU_AVAILABLE:
        # Fallback to standard Django LOGGING already configured in settings
        if isinstance(logger, logging.Logger):
            logger.info("Loguru or codex-core not found. Using standard Django logging.")
        return

    # Use codex-core setup
    service_name = getattr(settings, "PROJECT_NAME", "django-backend")
    adapter = DjangoLoggingSettingsAdapter()

    if os.name == "nt":
        _setup_windows_logging(adapter, service_name)
        return

    setup_logging(
        settings=adapter,
        service_name=service_name,
        intercept_loggers=["django", "django.server", "django.db.backends"],
        log_levels={
            "django.db.backends": logging.WARNING,
            "django.utils.autoreload": logging.WARNING,
            "django_lifecycle": logging.WARNING,
        },
    )

    if not isinstance(logger, logging.Logger):
        logger.info(f"Loguru initialized via codex-core for {service_name}")
