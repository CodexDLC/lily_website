"""
codex_tools.notifications.service
==================================
Notification management core.

Orchestrates the process: collects data via Builder and sends it
to the queue via Adapter. Acts as a base class for all notification
services in projects.
"""

from typing import Any

from .builder import NotificationPayloadBuilder


class BaseNotificationEngine:
    """
    Base notification engine.

    Framework-agnostic. All communication with the outside world (queues, DB)
    goes through the provided adapter.
    """

    TASK_NAME = "send_universal_notification_task"

    def __init__(self, adapter: Any):
        """
        Args:
            adapter: Object implementing the .enqueue(task_name, payload) method.
        """
        self.adapter = adapter

    def dispatch(self, **kwargs) -> bool:
        """
        Collects the data package and sends it to the queue.

        Args:
            **kwargs: Parameters for NotificationPayloadBuilder.build().

        Returns:
            bool: True if the task was successfully dequeued.
        """
        payload = NotificationPayloadBuilder.build(**kwargs)
        return self.adapter.enqueue(self.TASK_NAME, payload)
