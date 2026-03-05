"""
codex_tools.notifications.service
==================================
Ядро управления уведомлениями.

Оркестрирует процесс: собирает данные через Builder и отправляет их
в очередь через Adapter. Является базовым классом для всех сервисов
уведомлений в проектах.
"""

from typing import Any

from .builder import NotificationPayloadBuilder


class BaseNotificationEngine:
    """
    Базовый движок уведомлений.

    Не зависит от фреймворка. Вся связь с внешним миром (очереди, БД)
    идет через переданный адаптер.
    """

    TASK_NAME = "send_universal_notification_task"

    def __init__(self, adapter: Any):
        """
        Args:
            adapter: Объект, реализующий метод .enqueue(task_name, payload).
        """
        self.adapter = adapter

    def dispatch(self, **kwargs) -> bool:
        """
        Собирает пакет данных и отправляет его в очередь.

        Args:
            **kwargs: Параметры для NotificationPayloadBuilder.build().

        Returns:
            bool: True если задача успешно поставлена в очередь.
        """
        payload = NotificationPayloadBuilder.build(**kwargs)
        return self.adapter.enqueue(self.TASK_NAME, payload)
