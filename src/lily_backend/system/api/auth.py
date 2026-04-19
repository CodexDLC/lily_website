from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from django.conf import settings
from ninja.errors import HttpError

if TYPE_CHECKING:
    from collections.abc import Callable

SCOPE_TO_SETTING = {
    "tracking.flush": "TRACKING_WORKER_API_KEY",
    "conversations.import": "CONVERSATIONS_IMPORT_API_KEY",
    "booking.worker": "BOOKING_WORKER_API_KEY",
    "ops.worker": "OPS_WORKER_API_KEY",
}


def require_internal_scope(request: Any, scope: str) -> None:
    expected_setting = SCOPE_TO_SETTING.get(scope)
    expected = str(getattr(settings, expected_setting, "") if expected_setting else "")
    supplied_scope = request.headers.get("X-Internal-Scope", "")
    supplied_token = request.headers.get("X-Internal-Token", "")
    if not expected or supplied_scope != scope or not secrets.compare_digest(supplied_token, expected):
        raise HttpError(403, "Forbidden")


def internal_scope(scope: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            require_internal_scope(request, scope)
            return func(request, *args, **kwargs)

        return wrapper

    return decorator
