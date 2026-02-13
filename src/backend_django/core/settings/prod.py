"""
lily_website — Production Settings.

Inherits from base.py. Postgres, DEBUG=False, security hardened.
"""

import os
from typing import Any

from .base import *  # noqa: F401,F403

# ═══════════════════════════════════════════
# Security
# ═══════════════════════════════════════════

DEBUG = False

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ═══════════════════════════════════════════
# Database — PostgreSQL
# ═══════════════════════════════════════════

# Using type ignore for redefinition of DATABASES which is standard in Django settings
DATABASES: dict[str, dict[str, Any]] = {  # type: ignore[no-redef]
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "lily_website"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "postgres"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "options": f"-c search_path={os.environ.get('DB_SCHEMA', 'django_app')},public",
        },
    }
}

# ═══════════════════════════════════════════
# Static files
# ═══════════════════════════════════════════

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

# ═══════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
