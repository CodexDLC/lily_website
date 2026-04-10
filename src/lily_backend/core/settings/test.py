"""
Test settings — used only for pytest.

Inherits from base settings but uses SQLite in-memory for speed.
"""

from .base import *  # noqa: F403

# Enable debug mode in tests for detailed error pages
DEBUG = True

# Override ROOT_URLCONF — base uses "lily_backend.core.urls" which assumes
# the package is on sys.path, but pytest adds src/lily_backend directly.
ROOT_URLCONF = "core.urls"

# SQLite in-memory database for fast tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# In-memory cache for tests (no Redis)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# Disable Redis password for tests
REDIS_PASSWORD = None

# Email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable migrations for speed (optional)
# MIGRATION_MODULES = {app: None for app in INSTALLED_APPS}

# Fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Redis Isolation for Tests
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
