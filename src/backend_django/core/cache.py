from codex_tools.common.cache import get_cached_data_universal
from django.core.cache import cache


def get_cached_data(key: str, fetch_func, timeout: int = 60 * 60 * 24):
    """
    Django-specific wrapper for universal cache utility.
    """
    return get_cached_data_universal(
        cache_instance=cache, key=key, fetch_func=fetch_func, timeout=timeout, service_name="DjangoCache"
    )
