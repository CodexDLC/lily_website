"""Integration tests for appointment email-action views.

Covers:
- ConfirmAppointmentView (GET + POST: success + already-confirmed ValidationError)
- CancelAppointmentView (GET + POST: success redirect + already-cancelled error)
- CancelSuccessView (GET)
- RescheduleAppointmentView (GET)

Uses sqlite in-memory + Django test client with mocked notification dispatch.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse


@pytest.mark.integration
class TestConfirmAppointmentView:
    def test_get_renders_confirm_page(self, client, pending_appointment):
        pending_appointment.finalize_token = "CFMTOKEN"
        pending_appointment.save()

        resp = client.get(reverse("booking:booking_confirm", kwargs={"token": "CFMTOKEN"}))
        assert resp.status_code == 200

    def test_get_404_on_bad_token(self, client):
        resp = client.get(reverse("booking:booking_confirm", kwargs={"token": "NOTOKEN"}))
        assert resp.status_code == 404

    def test_post_confirms_pending_appointment(self, client, pending_appointment):
        pending_appointment.finalize_token = "CFMOK"
        pending_appointment.save()

        resp = client.post(reverse("booking:booking_confirm", kwargs={"token": "CFMOK"}))
        assert resp.status_code == 200

        pending_appointment.refresh_from_db()
        assert pending_appointment.status == "confirmed"

    def test_post_renders_success_true_in_context(self, client, pending_appointment):
        pending_appointment.finalize_token = "CFMSUCCESS"
        pending_appointment.save()

        resp = client.post(reverse("booking:booking_confirm", kwargs={"token": "CFMSUCCESS"}))
        assert resp.context["success"] is True

    def test_post_already_confirmed_returns_error(self, client, pending_appointment):
        pending_appointment.finalize_token = "CFMERR"
        pending_appointment.status = "confirmed"
        pending_appointment.save()

        resp = client.post(reverse("booking:booking_confirm", kwargs={"token": "CFMERR"}))
        assert resp.status_code == 200
        assert "error" in resp.context

    def test_post_404_on_bad_token(self, client):
        resp = client.post(reverse("booking:booking_confirm", kwargs={"token": "MISSING"}))
        assert resp.status_code == 404


@pytest.mark.integration
class TestCancelAppointmentView:
    """Tests for CancelAppointmentView.

    GET tests use rf (RequestFactory) directly because the cancel_appointment.html
    template references `booking_cancel_action` without the `booking:` namespace —
    an existing template bug that causes NoReverseMatch during full test-client render.
    POST tests go through the test client because they redirect, bypassing the template.
    """

    def test_get_returns_200_for_pending(self, db, pending_appointment, rf):
        from django.contrib.auth.models import AnonymousUser
        from features.booking.views import CancelAppointmentView

        pending_appointment.finalize_token = "CXLGET"
        pending_appointment.save()

        request = rf.get("/fake/")
        request.user = AnonymousUser()
        view = CancelAppointmentView.as_view()
        resp = view(request, token="CXLGET")
        assert resp.status_code == 200

    def test_get_can_cancel_true_for_pending(self, db, pending_appointment, rf):
        from django.contrib.auth.models import AnonymousUser
        from features.booking.views import CancelAppointmentView

        pending_appointment.finalize_token = "CXLCANOK"
        pending_appointment.save()

        request = rf.get("/fake/")
        request.user = AnonymousUser()
        resp = CancelAppointmentView.as_view()(request, token="CXLCANOK")
        assert resp.context_data["can_cancel"] is True

    def test_get_can_cancel_false_for_already_cancelled(self, db, pending_appointment, rf):
        from django.contrib.auth.models import AnonymousUser
        from features.booking.views import CancelAppointmentView

        pending_appointment.finalize_token = "CXLALR"
        pending_appointment.status = "cancelled"
        pending_appointment.save()

        request = rf.get("/fake/")
        request.user = AnonymousUser()
        resp = CancelAppointmentView.as_view()(request, token="CXLALR")
        assert resp.context_data["can_cancel"] is False

    def test_post_cancels_and_redirects(self, client, pending_appointment):
        pending_appointment.finalize_token = "CXLPOST"
        pending_appointment.save()

        with patch("features.conversations.services.notifications._get_engine") as mock_eng:
            mock_eng.return_value = MagicMock()
            resp = client.post(
                reverse("booking:booking_cancel_action", kwargs={"token": "CXLPOST"}),
                {"reason": "client", "note": "Changed my mind"},
            )

        assert resp.status_code == 302
        assert resp.url.endswith(reverse("booking:cancel_success"))

        pending_appointment.refresh_from_db()
        assert pending_appointment.status == "cancelled"
        assert pending_appointment.cancel_reason == "client"

    def test_post_dispatches_cancelled_event(self, client, pending_appointment):
        pending_appointment.finalize_token = "CXLEVT"
        pending_appointment.save()

        with patch("features.conversations.services.notifications._get_engine") as mock_eng:
            engine_mock = MagicMock()
            mock_eng.return_value = engine_mock
            client.post(
                reverse("booking:booking_cancel_action", kwargs={"token": "CXLEVT"}),
                {"reason": "client"},
            )
            engine_mock.dispatch_event.assert_called_once()
            event_name = engine_mock.dispatch_event.call_args[0][0]
            assert event_name == "booking.cancelled"

    def test_post_already_cancelled_returns_error(self, db, pending_appointment, rf):
        from django.contrib.auth.models import AnonymousUser
        from features.booking.views import CancelAppointmentView

        pending_appointment.finalize_token = "CXLALRERR"
        pending_appointment.status = "cancelled"
        pending_appointment.save()

        request = rf.post("/fake/", {"reason": "client"})
        request.user = AnonymousUser()
        resp = CancelAppointmentView.as_view()(request, token="CXLALRERR")
        assert resp.status_code == 200
        assert "error" in resp.context_data

    def test_get_404_on_bad_token(self, client):
        resp = client.get(reverse("booking:booking_cancel", kwargs={"token": "NOTOKEN"}))
        assert resp.status_code == 404

    def test_post_404_on_bad_token(self, client):
        resp = client.post(
            reverse("booking:booking_cancel_action", kwargs={"token": "NOTOKEN"}),
            {"reason": "client"},
        )
        assert resp.status_code == 404


@pytest.mark.integration
class TestCancelSuccessView:
    def test_get_renders_200(self, client):
        resp = client.get(reverse("booking:cancel_success"))
        assert resp.status_code == 200


@pytest.mark.integration
class TestRescheduleAppointmentView:
    def test_get_renders_reschedule_page(self, client, pending_appointment):
        pending_appointment.finalize_token = "RSCHTOKEN"
        pending_appointment.save()

        resp = client.get(reverse("booking:booking_reschedule", kwargs={"token": "RSCHTOKEN"}))
        assert resp.status_code == 200
        assert resp.context["appointment"].pk == pending_appointment.pk

    def test_get_404_on_bad_token(self, client):
        resp = client.get(reverse("booking:booking_reschedule", kwargs={"token": "BADTOKEN"}))
        assert resp.status_code == 404
