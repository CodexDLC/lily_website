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
        self.debug = getattr(settings, "DEBUG", False)
        # Default to DEBUG in development, INFO in production
        default_console_level = "DEBUG" if self.debug else "INFO"
        self.log_level_console = str(getattr(settings, "LOG_LEVEL_CONSOLE", default_console_level)).upper()
        self.log_level_file = str(getattr(settings, "LOG_LEVEL_FILE", "DEBUG")).upper()
        self.log_rotation = str(getattr(settings, "LOG_ROTATION", "10 MB"))
        self.log_dir = str(getattr(settings, "LOG_DIR", "logs"))


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

    # Set levels only — no individual handlers. All loggers propagate to root InterceptHandler.
    # Setting handlers on child loggers in the same chain causes each record to hit
    # InterceptHandler multiple times; the depth calculation overshoots and Loguru fails silently.
    logging.getLogger("django.server").setLevel(logging.INFO if adapter.debug else logging.WARNING)
    logging.getLogger("django.db.backends").setLevel(logging.INFO if adapter.debug else logging.WARNING)
    logging.getLogger("django.utils.autoreload").setLevel(logging.WARNING)
    logging.getLogger("django_lifecycle").setLevel(logging.INFO if adapter.debug else logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.INFO)

    logger.info(
        "Loguru initialized in Windows-safe mode for {}. Logs: {}",
        service_name,
        base_log_dir,
    )


def _get_debug_levels() -> dict[str, int]:
    """Verbose levels for development."""
    return {
        "django.server": logging.INFO,  # See requested URLs
        "django.db.backends": logging.INFO,  # See queries (INFO is usually enough for codex-core interceptor)
        "django.utils.autoreload": logging.WARNING,
        "django_lifecycle": logging.INFO,
        "asyncio": logging.INFO,
        "arq": logging.INFO,
    }


def _get_production_levels() -> dict[str, int]:
    """Quiet levels for production."""
    return {
        "django.server": logging.WARNING,
        "django.db.backends": logging.WARNING,
        "django.utils.autoreload": logging.ERROR,
        "django_lifecycle": logging.WARNING,
        "asyncio": logging.WARNING,
    }


def init_logging() -> None:
    """Initialize logging based on project settings and available libraries."""
    if getattr(settings, "DISABLE_PROJECT_LOGGING", False):
        return

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

    # Choose levels based on environment
    log_levels = _get_debug_levels() if adapter.debug else _get_production_levels()

    setup_logging(
        settings=adapter,
        service_name=service_name,
        intercept_loggers=["django", "django.server", "django.db.backends", "asyncio", "arq"],
        log_levels=log_levels,
    )

    if not isinstance(logger, logging.Logger):
        mode = "DEBUG" if adapter.debug else "PRODUCTION"
        logger.info(f"Loguru initialized ({mode} mode) via codex-core for {service_name}")
