"""
lily_backend — Production Settings.

Inherits from base.py. Postgres, DEBUG=False by default, security hardened.
"""

import os

from .base import *  # noqa: F403

# ═══════════════════════════════════════════
# Security
# ═══════════════════════════════════════════

# Allow overriding DEBUG from environment, but default to False for safety
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# HTTPS settings (only active if DEBUG is False)
if not DEBUG:
    # Trust X-Forwarded-Proto header from Nginx reverse proxy
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # We disable Django-level redirect because Nginx handles it.
    # This prevents 301 errors during internal Docker communication (e.g., Bot -> Backend)
    SECURE_SSL_REDIRECT = False

    SECURE_HSTS_SECONDS = 31_536_000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    LANGUAGE_COOKIE_SECURE = True

# TODO: Update with your production domain(s)
CSRF_TRUSTED_ORIGINS = [
    "https://example.com",
    "https://www.example.com",
]

# TODO: Update with your production domain
CSRF_COOKIE_DOMAIN = ".example.com"
SESSION_COOKIE_DOMAIN = ".example.com"

# ═══════════════════════════════════════════
# Static files
# ═══════════════════════════════════════════

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

# Adds content hash to filenames (e.g. app.abc123de.css)
# so nginx can cache forever and browsers always get fresh files on deploy
STORAGES = {
    "staticfiles": {
        "BACKEND": "core.storage.ProductionManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

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
