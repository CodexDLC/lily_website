from pathlib import Path
from typing import Any

from codex_tools.common.logger import setup_universal_logging
from loguru import logger

# Alias for convenience
log = logger


def setup_logging(base_dir: Path, config: dict[str, Any]) -> None:
    """
    Configures loguru for Django using codex_tools.
    """
    log_dir = base_dir / "logs" / "backend"

    setup_universal_logging(
        log_dir=log_dir,
        service_name="Django",
        console_level=config.get("LOG_LEVEL_CONSOLE", "INFO"),
        file_level=config.get("LOG_LEVEL_FILE", "DEBUG"),
        rotation=config.get("LOG_ROTATION", "10 MB"),
        is_debug=config.get("DEBUG", False),
    )
