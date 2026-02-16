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

    if not clean_domain.startswith("www."):
        www_domain = f"www.{clean_domain}"
        if www_domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(www_domain)

# ═══════════════════════════════════════════
# Application definition
# ═══════════════════════════════════════════

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
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

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

# ═══════════════════════════════════════════
# Redis & ARQ
# ═══════════════════════════════════════════

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

IS_INSIDE_DOCKER = os.path.exists("/.dockerenv")
if REDIS_HOST == "localhost" and IS_INSIDE_DOCKER:
    REDIS_HOST = "redis"

if REDIS_PASSWORD:
    clean_password = REDIS_PASSWORD.strip("'\"").strip()
    encoded_password = quote_plus(clean_password)
    REDIS_URL = f"redis://:{encoded_password}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# ═══════════════════════════════════════════
# Unfold Configuration
# ═══════════════════════════════════════════

UNFOLD = {
    "SITE_TITLE": "LILY Beauty Salon Admin",
    "SITE_HEADER": "LILY Beauty",
    "SITE_SYMBOL": "spa",
    "COLORS": {
        "primary": {
            "50": "239, 246, 255",
            "100": "219, 234, 254",
            "200": "191, 219, 254",
            "300": "147, 197, 253",
            "400": "96, 165, 250",
            "500": "59, 130, 246",
            "600": "37, 99, 235",
            "700": "29, 78, 216",
            "800": "30, 64, 175",
            "900": "30, 58, 138",
            "950": "23, 37, 84",
        },
    },
    # PWA: Подключение кастомных стилей для мобильной адаптации
    "STYLES": [
        lambda request: "/static/css/admin/pwa-mobile.css",  # Мобильные оптимизации
    ],
    # PWA: Подключение кастомных скриптов для PWA функциональности
    "SCRIPTS": [
        lambda request: "/static/js/admin/pwa-enhance.js",
    ],
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Salon Management",
                "items": [
                    {
                        "title": "Appointments",
                        "icon": "calendar_month",
                        "link": "/admin/booking/appointment/",
                        "permission": lambda request: request.user.has_perm("booking.view_appointment"),
                    },
                    {
                        "title": "Masters",
                        "icon": "face",
                        "link": "/admin/booking/master/",
                        "permission": lambda request: request.user.has_perm("booking.view_master"),
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": "/admin/main/category/",
                        "permission": lambda request: request.user.has_perm("main.view_category"),
                    },
                    {
                        "title": "Services",
                        "icon": "content_cut",
                        "link": "/admin/main/service/",
                        "permission": lambda request: request.user.has_perm("main.view_service"),
                    },
                ],
            },
            {
                "title": "System & Users",
                "items": [
                    {
                        "title": "Clients",
                        "icon": "group",
                        "link": "/admin/booking/client/",
                        "permission": lambda request: request.user.has_perm("booking.view_client"),
                    },
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": "/admin/auth/user/",
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Site Settings",
                        "icon": "settings",
                        "link": "/admin/system/sitesettings/",
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },
    # Расширения для мультиязычности (флаги языков)
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "de": "🇩🇪",
                "ru": "🇷🇺",
                "uk": "🇺🇦",
            },
        },
    },
}

# ═══════════════════════════════════════════
# Cache & Sessions
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
# Logging
# ═══════════════════════════════════════════

LOGGING_CONFIG = None
LOG_LEVEL_CONSOLE = os.environ.get("LOG_LEVEL", "INFO")
LOG_LEVEL_FILE = "DEBUG"
LOG_ROTATION = "10 MB"
