import os
from pathlib import Path

from .security import DEBUG

IS_DOCKER = os.environ.get("IS_DOCKER", "False").lower() in ("true", "1", "t") or os.path.exists("/.dockerenv")

# Root of the whole project (lily_website)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent

# ═══════════════════════════════════════════
# Logging (codex-core compatible)
# ═══════════════════════════════════════════

# Loguru / codex-core compatible fields (used in core/logger.py)
LOG_LEVEL_CONSOLE = os.environ.get("LOG_LEVEL_CONSOLE", "DEBUG" if DEBUG else "INFO")
LOG_LEVEL_FILE = os.environ.get("LOG_LEVEL_FILE", "DEBUG")
LOG_ROTATION = os.environ.get("LOG_ROTATION", "10 MB")
LOG_DIR = os.environ.get("LOG_DIR", str(ROOT_DIR / "logs" if not IS_DOCKER else "/app/logs"))

# Standard Django LOGGING (fallback if loguru is disabled/missing)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL_CONSOLE,
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
