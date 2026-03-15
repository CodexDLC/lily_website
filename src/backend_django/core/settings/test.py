"""
Test settings - используется только для pytest.

Наследуется от base settings, но использует SQLite in-memory для скорости.
"""

from .base import *  # noqa: F403

# DEBUG=True for detailed error pages, but we guard against debug_toolbar
# import in urls.py (debug_toolbar is only in dev.py INSTALLED_APPS)
DEBUG = True

# Prevent debug_toolbar from being loaded in test environment
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda _: False}
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

# SQLite in-memory database для быстрых тестов
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# In-memory cache для тестов (без Redis)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# Отключаем пароль Redis для тестов
REDIS_PASSWORD = None

# Email backend для тестов
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Отключаем миграции для скорости (опционально)
# MIGRATION_MODULES = {app: None for app in INSTALLED_APPS}

# Быстрый хэшер паролей для тестов
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
