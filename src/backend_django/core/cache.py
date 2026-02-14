from django.core.cache import cache
from loguru import logger as log


def get_cached_data(key: str, fetch_func, timeout: int = 60 * 60 * 24):
    """
    Универсальная функция для кэширования данных.
    - key: Уникальный ключ для Redis.
    - fetch_func: Функция, которая вызывается, если данных нет в кэше.
    - timeout: Время жизни кэша (по умолчанию 24 часа).
    """
    data = cache.get(key)

    if data is not None:
        log.debug(f"Cache | action=get status=hit key='{key}'")
        return data

    log.debug(f"Cache | action=get status=miss key='{key}'")

    # Получаем свежие данные
    data = fetch_func()

    # Сохраняем в кэш
    if data is not None:
        # Если это QuerySet, превращаем его в список, чтобы он "застыл" для кэша
        if hasattr(data, "all") and callable(data.all):
            data = list(data)

        cache.set(key, data, timeout)
        log.debug(f"Cache | action=set status=success key='{key}' timeout={timeout}")

    return data
