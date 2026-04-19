from codex_django.tracking.flush import flush_page_views
from ninja import Router

from .auth import require_internal_scope

router = Router(tags=["Tracking"])


@router.post("/flush", summary="Flush page view counters from Redis to DB")
def flush_tracking(request) -> dict:
    require_internal_scope(request, "tracking.flush")
    count = flush_page_views()
    return {"flushed": count}
