"""
Test settings - используется только для pytest.

Наследуется от dev settings, но использует SQLite in-memory для скорости.
"""

from .dev import *  # noqa: F403

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
