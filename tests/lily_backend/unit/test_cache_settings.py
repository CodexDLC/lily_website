from core.settings.modules import cache


def test_runtime_cache_uses_codex_django_redis_backend():
    default_cache = cache.CACHES["default"]

    assert default_cache["BACKEND"] == "codex_django.cache.backends.redis.RedisCache"
    assert default_cache["LOCATION"] == cache.REDIS_URL
    assert default_cache["KEY_PREFIX"] == cache.PROJECT_NAME
    assert default_cache["TIMEOUT"] == 300
    assert "OPTIONS" not in default_cache


def test_runtime_sessions_use_codex_django_redis_backend():
    assert cache.SESSION_ENGINE == "codex_django.sessions.backends.redis"
    assert not hasattr(cache, "SESSION_CACHE_ALIAS")
