from __future__ import annotations

from django.utils import timezone


class TrackingRecorder:
    @staticmethod
    def record(request) -> None:
        from .manager import get_tracking_manager

        today = timezone.now().strftime("%Y-%m-%d")
        user_id = str(request.user.pk) if request.user.is_authenticated else None
        get_tracking_manager().record(request.path, today, user_id)
