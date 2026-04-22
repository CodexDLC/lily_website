import pytest
from django.test import RequestFactory, override_settings
from ninja.errors import HttpError
from system.api.auth import require_internal_scope


@override_settings(
    TRACKING_WORKER_API_KEY="tracking-token",  # pragma: allowlist secret
    CONVERSATIONS_IMPORT_API_KEY="mail-token",  # pragma: allowlist secret
)
def test_internal_scope_accepts_matching_token():
    request = RequestFactory().post(
        "/api/v1/tracking/flush",
        HTTP_X_INTERNAL_SCOPE="tracking.flush",
        HTTP_X_INTERNAL_TOKEN="tracking-token",
    )

    require_internal_scope(request, "tracking.flush")


@override_settings(
    TRACKING_WORKER_API_KEY="tracking-token",  # pragma: allowlist secret
    CONVERSATIONS_IMPORT_API_KEY="mail-token",  # pragma: allowlist secret
)
def test_internal_scope_rejects_cross_scope_token():
    request = RequestFactory().post(
        "/api/v1/tracking/flush",
        HTTP_X_INTERNAL_SCOPE="tracking.flush",
        HTTP_X_INTERNAL_TOKEN="mail-token",
    )

    with pytest.raises(HttpError):
        require_internal_scope(request, "tracking.flush")
