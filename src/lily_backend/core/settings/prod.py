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

DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "").strip()
if DOMAIN_NAME:
    SITE_BASE_URL = os.environ.get("SITE_BASE_URL", f"https://{DOMAIN_NAME}/")  # noqa: F405
    CSRF_TRUSTED_ORIGINS = [
        f"https://{DOMAIN_NAME}",
        f"https://www.{DOMAIN_NAME}",
    ]

# Keep cookies host-only on the canonical non-www domain unless explicitly
# overridden. This avoids issuing duplicate CSRF/session cookies across
# host-only + domain-scoped variants.
SESSION_COOKIE_DOMAIN = os.environ.get("SESSION_COOKIE_DOMAIN") or None
CSRF_COOKIE_DOMAIN = os.environ.get("CSRF_COOKIE_DOMAIN") or None

# Use a fresh CSRF cookie name in production so browsers with a stale duplicate
# `csrftoken` stop sending the old conflicting value after deploy.
CSRF_COOKIE_NAME = os.environ.get("CSRF_COOKIE_NAME", "csrftoken_app")

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
# Cache & Sessions
# ═══════════════════════════════════════════

# Toggle for using custom Codex Redis backends for cache and sessions.
# If False, falls back to standard django-redis and database sessions.
USE_CODEX_REDIS_BACKENDS = os.environ.get("USE_CODEX_REDIS_BACKENDS", "False").lower() in ("true", "1", "yes")

if USE_CODEX_REDIS_BACKENDS:
    CACHES = {
        "default": {
            "BACKEND": "codex_django.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,  # noqa: F405
            "KEY_PREFIX": PROJECT_NAME,  # noqa: F405
            "TIMEOUT": 300,
        }
    }
    SESSION_ENGINE = "codex_django.sessions.backends.redis"
else:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,  # noqa: F405
            "KEY_PREFIX": PROJECT_NAME,  # noqa: F405
            "TIMEOUT": 300,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }

    SESSION_ENGINE = "django.contrib.sessions.backends.db"

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
