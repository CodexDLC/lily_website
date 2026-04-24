"""Bot logging setup — wraps codex_core.common.loguru_setup with PII masking."""

import logging
import re

from codex_core.common.loguru_setup import setup_logging
from loguru import logger

from src.telegram_bot.core.config import BotSettings

__all__ = ["setup_bot_logging"]

_BOT_INTERCEPT_LOGGERS = ["uvicorn.access", "uvicorn.error", "arq", "arq.worker"]
_BOT_LOG_LEVELS = {
    "aiogram": logging.INFO,
    "sqlalchemy": logging.WARNING,
    "httpx": logging.WARNING,
    "aiosqlite": logging.INFO,
    "arq": logging.INFO,
    "asyncio": logging.INFO,
}


def _mask_sensitive_data(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = re.sub(r"(\+?\d{1,3}[\s-]?\d{3})[\s-]?\d{3,}[\s-]?(\d{2,4})", r"\1 *** \2", text)
    text = re.sub(r"([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", r"\1***@\2", text)
    text = re.sub(
        r"(?i)(password|token|secret|api_key|key|authorization|cookie|session_id)"
        r'([\s:=("]*)'
        r'([^\s,;}"\']{4,})',
        r"\1\2***",
        text,
    )
    return text


def setup_bot_logging(settings: BotSettings, service_name: str = "telegram_bot") -> None:
    """Configure Loguru for the bot with PII masking and codex-core sinks."""
    setup_logging(
        settings=settings,
        service_name=service_name,
        intercept_loggers=_BOT_INTERCEPT_LOGGERS,
        log_levels=_BOT_LOG_LEVELS,
    )
    logger.configure(patcher=lambda record: record.update(message=_mask_sensitive_data(record["message"])))
