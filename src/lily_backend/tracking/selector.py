from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from .manager import get_tracking_manager

"""
TrackingSelector — read-only queries over tracking data.
Uses TrackingRedisManager; no direct DB queries.
"""


class TrackingSelector:
    @staticmethod
    def top_pages(date_str: str | None = None, limit: int = 10) -> list[dict]:
        today = date_str or timezone.now().strftime("%Y-%m-%d")
        raw = get_tracking_manager().get_daily(today)
        if not raw:
            return []
        items = sorted(raw.items(), key=lambda x: int(x[1]), reverse=True)
        return [{"path": path, "views": int(views)} for path, views in items[:limit]]

    @staticmethod
    def unique_visitors(date_str: str | None = None) -> int:
        today = date_str or timezone.now().strftime("%Y-%m-%d")
        return get_tracking_manager().get_unique_count(today)

    @staticmethod
    def total_views(date_str: str | None = None) -> int:
        today = date_str or timezone.now().strftime("%Y-%m-%d")
        raw = get_tracking_manager().get_daily(today)
        return sum(int(v) for v in raw.values()) if raw else 0

    @staticmethod
    def multi_day_totals(days: int = 7) -> list[dict]:
        today = timezone.now().date()
        dates = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
        snapshots = get_tracking_manager().get_multi_day(dates)
        return [
            {"date": d, "views": sum(int(v) for v in snap.values()) if snap else 0}
            for d, snap in zip(dates, snapshots, strict=False)
        ]
