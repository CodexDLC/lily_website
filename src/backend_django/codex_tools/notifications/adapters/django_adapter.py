"""
codex_tools.notifications.adapters.django_adapter
==================================================
Реализация адаптера для Django.

Связывает универсальное ядро уведомлений с инфраструктурой Django.
НЕ содержит жестких импортов из ядра проекта (core.*).
"""

from collections.abc import Callable
from typing import Any

from django.core.cache import cache
from django.utils.translation import override


class DjangoNotificationAdapter:
    """
    Адаптер для интеграции Notification Engine в Django-проект.
    """

    def __init__(self, enqueue_func: Callable[[str, dict], Any]):
        """
        Args:
            enqueue_func: Функция для постановки задачи в очередь (например, DjangoArqClient.enqueue_job).
        """
        self.enqueue_func = enqueue_func

    def enqueue(self, task_name: str, payload: dict) -> bool:
        """Постановка задачи в очередь через переданную функцию."""
        try:
            self.enqueue_func(task_name, payload_dict=payload)
            return True
        except Exception:
            return False

    @staticmethod
    def get_cached_value(key: str) -> str | None:
        """Получение текста из кэша Django."""
        return cache.get(f"email_content_{key}")

    @staticmethod
    def set_cached_value(key: str, value: str, timeout: int):
        """Сохранение текста в кэш Django."""
        cache.set(f"email_content_{key}", value, timeout)

    @staticmethod
    def translation_override(lang: str):
        """Контекстный менеджер для смены языка на лету."""
        return override(lang)
