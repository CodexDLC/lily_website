import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from src.shared.core.config import CommonSettings

if TYPE_CHECKING:
    from types import FrameType


def mask_sensitive_data(text: str) -> str:
    """
    Masks sensitive data in text (phones, emails, passwords, tokens).
    """
    if not isinstance(text, str):
        return text

    # 1. Mask phones (RU/DE/International)
    # Example: +49 176 12345678 -> +49 176 *** 5678
    phone_pattern = r"(\+?\d{1,3}[\s-]?\d{3})[\s-]?\d{3,}[\s-]?(\d{2,4})"
    text = re.sub(phone_pattern, r"\1 *** \2", text)

    # 2. Mask Emails
    # Example: user@example.com -> u***@example.com
    email_pattern = r"([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
    text = re.sub(email_pattern, r"\1***@\2", text)

    # 3. Mask sensitive keys (password, token, secret, key, api_key)
    # Looks for patterns like password=value, "token": "value", secret: value
    sensitive_keys_pattern = (
        r"(?i)(password|token|secret|api_key|key|authorization|cookie|session_id)"
        r'([\s:=("]*)'  # Separators
        r'([^\s,;}"\']{4,})'  # The value itself (min 4 chars to avoid masking empty or too short values)
    )
    text = re.sub(sensitive_keys_pattern, r"\1\2***", text)

    return text


def masking_patcher(record):
    """
    Loguru patcher that masks the message before output.
    """
    record["message"] = mask_sensitive_data(record["message"])


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


def setup_logging(settings: CommonSettings, service_name: str) -> None:
    """
    Configures loguru with data masking.

    Args:
        settings: Settings object (CommonSettings or descendant).
        service_name: Service name ('backend' or '02_telegram_bot').
                      Used for creating a subfolder in logs.
    """
    logger.remove()

    # Apply masking to all logs via patcher
    logger.configure(patcher=masking_patcher)

    # Form log paths: logs/backend/debug.log or logs/02_telegram_bot/debug.log
    base_log_dir = Path(settings.log_dir) / service_name

    log_file_debug = base_log_dir / "debug.log"
    log_file_errors = base_log_dir / "errors.json"

    # Console output (common format)
    logger.add(
        sink=sys.stdout,
        level=settings.log_level_console.upper(),
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            f"<magenta>{service_name}</magenta> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # Debug file
    logger.add(
        sink=str(log_file_debug),
        level=settings.log_level_file.upper(),
        rotation=settings.log_rotation,
        compression="zip",
        format="{time} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    # Errors file (JSON)
    logger.add(
        sink=str(log_file_errors),
        level="ERROR",
        serialize=True,
        rotation=settings.log_rotation,
        compression="zip",
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # Intercept library logs
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    logging.getLogger("arq").handlers = [InterceptHandler()]
    logging.getLogger("arq.worker").handlers = [InterceptHandler()]

    # Configure levels for libraries
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.INFO)
    logging.getLogger("arq").setLevel(logging.INFO)

    logger.info(f"LoggerSetup | service={service_name} status=success path='{base_log_dir}'")
