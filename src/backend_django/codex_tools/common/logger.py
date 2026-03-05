"""
codex_tools.common.logger
==========================
Универсальная настройка Loguru для Python проектов.

Поддерживает:
- Перехват стандартного модуля logging.
- Красивый вывод в консоль.
- Ротацию и сжатие логов.
- JSON формат для ошибок.
"""

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from types import FrameType


class InterceptHandler(logging.Handler):
    """
    Перехватывает сообщения стандартного logging и перенаправляет в loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = logging.currentframe()
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_universal_logging(
    log_dir: Path,
    service_name: str = "App",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    rotation: str = "10 MB",
    is_debug: bool = False,
) -> None:
    """
    Настраивает loguru с перехватом стандартных логов.
    """
    logger.remove()
    log_dir.mkdir(parents=True, exist_ok=True)

    # 1. Console output
    logger.add(
        sink=sys.stdout,
        level=console_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            f"<magenta>{service_name}</magenta> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # 2. Debug file
    logger.add(
        sink=str(log_dir / "debug.log"),
        level=file_level,
        rotation=rotation,
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
        backtrace=is_debug,
        diagnose=is_debug,
    )

    # 3. Errors file (JSON)
    logger.add(
        sink=str(log_dir / "errors.json"),
        level="ERROR",
        serialize=True,
        rotation=rotation,
        compression="zip",
        enqueue=True,
    )

    # 4. Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Silence noisy libraries
    for lib in ["django", "urllib3", "asyncio"]:
        logging.getLogger(lib).setLevel(logging.INFO)

    logging.getLogger("django.db.backends").setLevel(logging.WARNING)

    logger.info(f"Loguru setup complete for {service_name}. Logs: {log_dir}")
