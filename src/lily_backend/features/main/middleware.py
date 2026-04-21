from typing import Any

from features.main.cabinet import refresh_catalog_categories


class CabinetRefreshMiddleware:
    """
    Middleware that triggers a one-time refresh of the cabinet sidebar
    categories for each process. This ensures that dynamic items are
    loaded from the DB at least once at runtime, without doing so during
    Django initialization (which triggers RuntimeWarnings).
    """

    _refreshed = False

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        if not self._refreshed:
            refresh_catalog_categories()
            CabinetRefreshMiddleware._refreshed = True

        return self.get_response(request)
