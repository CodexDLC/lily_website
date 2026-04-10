from __future__ import annotations

from core.logger import logger
from django.conf import settings

_DEFAULTS: dict = {
    "skip_prefixes": ["/static/", "/media/", "/favicon", "/__debug__", "/admin/jsi18n"],
    "track_anonymous": False,
    "redis_alias": "default",
}

"""
PageTrackingMiddleware — library-ready.

Project connects via settings only:
    MIDDLEWARE += ["tracking.middleware.PageTrackingMiddleware"]

Optional settings.CABINET_TRACKING dict:
    {
        "skip_prefixes": ["/static/", "/media/"],  # default
        "track_anonymous": False,                   # default
        "redis_alias": "default",                   # default
    }
"""


class PageTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        cfg = getattr(settings, "CABINET_TRACKING", {})
        self.skip = cfg.get("skip_prefixes", _DEFAULTS["skip_prefixes"])
        self.track_anonymous = cfg.get("track_anonymous", _DEFAULTS["track_anonymous"])

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if self._should_track(request, response):
                from .recorder import TrackingRecorder

                TrackingRecorder.record(request)
        except Exception:
            # Never break the response over tracking errors, but log it
            logger.exception("Tracking recording failed")
        return response

    def _should_track(self, request, response) -> bool:
        if request.method != "GET":
            return False
        if response.status_code not in (200, 301, 302):
            return False
        if any(request.path.startswith(p) for p in self.skip):
            return False
        user = getattr(request, "user", None)
        return not (user is None or (not self.track_anonymous and not user.is_authenticated))
