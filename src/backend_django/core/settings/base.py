"""
lily_website — Base Settings.

Common settings for all environments.
Secrets and env-specific values loaded from .env via os.environ.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import dj_database_url
from dotenv import load_dotenv

# ═══════════════════════════════════════════
# Paths
# ═══════════════════════════════════════════

# In container: /app. Locally: src/backend_django
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from PROJECT ROOT (two levels up from src/backend_django)
load_dotenv(BASE_DIR.parent.parent / ".env")

# ═══════════════════════════════════════════
# Security
# ═══════════════════════════════════════════

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-CHANGE-ME")

# Main switch for the whole system
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

# --- Smart ALLOWED_HOSTS ---
# We start with safe defaults. 0.0.0.0 is removed for security.
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend"]

env_hosts = os.environ.get("ALLOWED_HOSTS", "")
if env_hosts:
    ALLOWED_HOSTS.extend([h.strip() for h in env_hosts.split(",") if h.strip()])

SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "http://127.0.0.1:8000/")
if not SITE_BASE_URL.endswith("/"):
    SITE_BASE_URL += "/"

domain = urlparse(SITE_BASE_URL).netloc
if domain:
    clean_domain = domain.split(":")[0]
    if clean_domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(clean_domain)

    # Automatically add www version for subdomain support
    if not clean_domain.startswith("www."):
        www_domain = f"www.{clean_domain}"
        if www_domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(www_domain)

# ═══════════════════════════════════════════
# Application definition
# ═══════════════════════════════════════════

INSTALLED_APPS = [
    "django_prometheus",
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "features.main",
    "features.system",
    "features.booking",
    "ninja",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
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
                "django.template.context_processors.i18n",
                "features.system.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# ═══════════════════════════════════════════
# Database
# ═══════════════════════════════════════════

# If DATABASE_URL is provided (Production/Neon), use it.
# Otherwise, fall back to local SQLite.
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # Add schema support if provided
    db_schema = os.environ.get("DB_SCHEMA", "public")
    DATABASES["default"]["OPTIONS"] = {"options": f"-c search_path={db_schema},public"}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
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
# Redis & ARQ (Task Queue)
# ═══════════════════════════════════════════

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

# Smart host detection for Docker
IS_INSIDE_DOCKER = os.path.exists("/.dockerenv")
if REDIS_HOST == "localhost" and IS_INSIDE_DOCKER:
    REDIS_HOST = "redis"

# Construct Redis URL with password encoding
if REDIS_PASSWORD:
    # Очищаем от кавычек и экранируем спецсимволы (например, '*')
    clean_password = REDIS_PASSWORD.strip("'\"").strip()
    encoded_password = quote_plus(clean_password)
    REDIS_URL = f"redis://:{encoded_password}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# ═══════════════════════════════════════════
# Cache & Sessions (Redis)
# ═══════════════════════════════════════════

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ═══════════════════════════════════════════
# Internationalization
# ═══════════════════════════════════════════

LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE", "de")
TIME_ZONE = os.environ.get("TIME_ZONE", "Europe/Berlin")
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("de", "Deutsch"),
    ("ru", "Russian"),
    ("uk", "Ukrainian"),
    ("en", "English"),
]

MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE.split("-")[0]
MODELTRANSLATION_LANGUAGES = ("de", "ru", "uk", "en")

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# ═══════════════════════════════════════════
# Static & Media
# ═══════════════════════════════════════════

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ═══════════════════════════════════════════
# Logging (Loguru)
# ═══════════════════════════════════════════

LOGGING_CONFIG = None
LOG_LEVEL_CONSOLE = os.environ.get("LOG_LEVEL", "INFO")
LOG_LEVEL_FILE = "DEBUG"
LOG_ROTATION = "10 MB"
