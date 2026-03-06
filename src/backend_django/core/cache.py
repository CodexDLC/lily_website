from codex_tools.common.cache import get_cached_data_universal
from django.core.cache import caches


def get_cached_data(key: str, fetch_func, timeout: int = 60 * 60 * 24):
    """
    Django-specific wrapper for universal cache utility.
    Uses the default cache backend directly to avoid recursion with Debug Toolbar.
    """
    default_cache = caches["default"]
    return get_cached_data_universal(
        cache_instance=default_cache, key=key, fetch_func=fetch_func, timeout=timeout, service_name="DjangoCache"
    )
