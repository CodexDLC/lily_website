from __future__ import annotations

from django.utils import timezone


def flush_page_views(date_str: str | None = None) -> int:
    """
    Read daily page view counters from Redis and upsert into PageView table.
    Returns number of paths flushed.

    Called by:
      - management command: python manage.py flush_page_views
      - ARQ task (TODO): tracking.tasks.flush_tracking_to_db
    """
    from .manager import get_tracking_manager
    from .models import PageView

    today = date_str or timezone.now().strftime("%Y-%m-%d")
    raw = get_tracking_manager().get_daily(today)
    if not raw:
        return 0

    PageView.objects.bulk_create(
        [PageView(path=path, date=today, views=int(views)) for path, views in raw.items()],
        update_conflicts=True,
        update_fields=["views"],
        unique_fields=["path", "date"],
    )
    return len(raw)
