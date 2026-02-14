"""
lily_website — Production Settings.

Inherits from base.py. Postgres, DEBUG=False by default, security hardened.
"""

import os

from .base import *  # noqa: F401,F403

# ═══════════════════════════════════════════
# Security
# ═══════════════════════════════════════════

# Allow overriding DEBUG from environment, but default to False for safety
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# HTTPS settings (only active if DEBUG is False)
if not DEBUG:
    # Trust X-Forwarded-Proto header from Nginx reverse proxy
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31_536_000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

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
