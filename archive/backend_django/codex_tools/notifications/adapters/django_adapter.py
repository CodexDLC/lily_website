"""
codex_tools.notifications.adapters.django_adapter
==================================================
Adapter implementation for Django.

Connects the universal notification core with Django infrastructure.
Does NOT contain hard imports from the project core (core.*).
"""

from collections.abc import Callable
from typing import Any

from django.core.cache import cache
from django.utils.translation import override


class DjangoNotificationAdapter:
    """
    Adapter for integrating the Notification Engine into a Django project.
    """

    def __init__(self, enqueue_func: Callable[[str, dict], Any]):
        """
        Args:
            enqueue_func: Function to enqueue the task (e.g., DjangoArqClient.enqueue_job).
        """
        self.enqueue_func = enqueue_func

    def enqueue(self, task_name: str, payload: dict) -> bool:
        """Enqueue the task via the provided function."""
        try:
            self.enqueue_func(task_name, payload_dict=payload)
            return True
        except Exception:
            return False

    @staticmethod
    def get_cached_value(key: str) -> str | None:
        """Retrieving text from Django cache."""
        return cache.get(f"email_content_{key}")

    @staticmethod
    def set_cached_value(key: str, value: str, timeout: int):
        """Saving text to Django cache."""
        cache.set(f"email_content_{key}", value, timeout)

    @staticmethod
    def translation_override(lang: str):
        """Context manager for on-the-fly language switching."""
        return override(lang)
