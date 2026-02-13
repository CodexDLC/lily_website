"""
lily_website — Base Settings.

Common settings for all environments.
Secrets and env-specific values loaded from .env via os.environ.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ═══════════════════════════════════════════
# Paths
# ═══════════════════════════════════════════

# In container: /app. Locally: src/backend_django
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from backend root
load_dotenv(BASE_DIR / ".env")

# ═══════════════════════════════════════════
# Security
# ═══════════════════════════════════════════

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-CHANGE-ME")

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# ═══════════════════════════════════════════
# Site Base URL
# ═══════════════════════════════════════════

SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "http://127.0.0.1:8000/")
if not SITE_BASE_URL.endswith("/"):
    SITE_BASE_URL += "/"

# ═══════════════════════════════════════════
# Application definition
# ═══════════════════════════════════════════

INSTALLED_APPS = [
    # ── Translation (must be before admin) ──
    "modeltranslation",
    # ── Django ──
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # ── Features ──
    "core",  # Core app (for AppConfig & Logging)
    "features.main",
    "features.system",
    "features.booking",
    # ── API ──
    "ninja",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Added for i18n
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",  # Added for i18n
                "features.system.context_processors.site_settings",  # Global Site Settings
                "core.context_processors.site_base_url",  # Custom context processor for SITE_BASE_URL
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# ═══════════════════════════════════════════
# Database
# ═══════════════════════════════════════════

# Supports both SQLite (dev) and PostgreSQL (prod/docker)
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

# ═══════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ═══════════════════════════════════════════
# Internationalization
# ═══════════════════════════════════════════

LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE", "de")  # Default to German
TIME_ZONE = os.environ.get("TIME_ZONE", "Europe/Berlin")
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("de", "Deutsch"),
    ("ru", "Russian"),
    ("uk", "Ukrainian"),
    ("en", "English"),
]

# Model Translation (django-modeltranslation)
MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE.split("-")[0]
MODELTRANSLATION_LANGUAGES = ("de", "ru", "uk", "en")

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# ═══════════════════════════════════════════
# Static files
# ═══════════════════════════════════════════

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ═══════════════════════════════════════════
# Media files
# ═══════════════════════════════════════════

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ═══════════════════════════════════════════
# Default primary key
# ═══════════════════════════════════════════

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ═══════════════════════════════════════════
# Environment
# ═══════════════════════════════════════════

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# ═══════════════════════════════════════════
# Redis & ARQ (Task Queue)
# ═══════════════════════════════════════════

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

# Автоматически определять хост на основе окружения
if REDIS_HOST == "localhost" and ENVIRONMENT == "production":
    REDIS_HOST = "redis"  # Docker service name

# Construct Redis URL
if REDIS_PASSWORD:
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# ═══════════════════════════════════════════
# Cache & Sessions (Redis)
# ═══════════════════════════════════════════

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# Store sessions in Redis
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ═══════════════════════════════════════════
# Telegram Integration
# ═══════════════════════════════════════════

TELEGRAM_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", None)

# ═══════════════════════════════════════════
# Logging (Loguru)
# ═══════════════════════════════════════════

# Disable Django's default logging configuration
LOGGING_CONFIG = None

# Loguru Settings
LOG_LEVEL_CONSOLE = os.environ.get("LOG_LEVEL", "INFO")
LOG_LEVEL_FILE = "DEBUG"
LOG_ROTATION = "10 MB"
