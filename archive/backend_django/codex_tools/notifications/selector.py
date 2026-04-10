"""
codex_tools.notifications.selector
===================================
Механизм получения локализованного контента.

Обеспечивает доступ к текстовым блокам писем (приветствия, подписи, тела писем)
с поддержкой мультиязычности и кэширования. Не зависит от конкретной ORM
благодаря использованию адаптера.
"""

from typing import Any


class BaseEmailContentSelector:
    """
    Базовый класс для выбора контента уведомлений.

    Логика:
    1. Ищем в кэше через адаптер.
    2. Если нет — ищем в БД через переданную модель.
    3. Сохраняем в кэш.
    """

    CACHE_TIMEOUT = 3600
    CACHE_PREFIX = "email_content_"

    def __init__(self, model_class: Any, adapter: Any):
        """
        Args:
            model_class: Класс модели (например, EmailContent).
            adapter: Экземпляр адаптера (например, DjangoNotificationAdapter).
        """
        self.model_class = model_class
        self.adapter = adapter

    def get_value(self, key: str, default: str = "") -> str:
        """
        Возвращает переведенный текст по ключу.

        Args:
            key: Уникальный идентификатор блока (например, 'ct_receipt_body').
            default: Значение по умолчанию, если ключ не найден.
        """
        # Пытаемся получить из кэша через адаптер
        cached_val = self.adapter.get_cached_value(key)
        if cached_val is not None:
            return cached_val

        try:
            # Пытаемся получить из БД (предполагается интерфейс Django ORM)
            obj = self.model_class.objects.get(key=key)
            val = obj.text
            # Сохраняем в кэш через адаптер
            self.adapter.set_cached_value(key, val, self.CACHE_TIMEOUT)
            return val
        except Exception:
            return default
