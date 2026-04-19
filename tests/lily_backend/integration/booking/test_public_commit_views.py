"""Integration tests for BookingCommitView and success pages.

Uses sqlite in-memory + Django test client with mocked gateway.create_booking
so we don't need real availability engine wiring.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from features.booking.dto.public_cart import (
    MODE_MULTI_DAY,
    MODE_SAME_DAY,
    SESSION_KEY,
    PublicCart,
    PublicCartItem,
)


def _store_cart(client, cart: PublicCart) -> None:
    session = client.session
    session[SESSION_KEY] = cart.to_dict()
    session.save()


def _cart_with_slot(service, *, mode=MODE_SAME_DAY) -> PublicCart:
    """Cart ready for commit (same_day mode)."""
    cart = PublicCart(mode=mode, stage=3, date="2026-06-15", time="10:00")
    cart.add(
        PublicCartItem(
            service_id=service.pk,
            service_title=service.name,
            duration=service.duration,
            price=service.price,
        )
    )
    return cart


def _valid_contact() -> dict:
    return {
        "first_name": "Anna",
        "last_name": "Testova",
        "phone": "+49111999888",
        "email": "",
        "client_notes": "",
        "cancellation_policy": "on",
        "consent": "on",
    }


def _mock_appointment(token: str = "TOKEN123") -> MagicMock:
    appt = MagicMock()
    appt.finalize_token = token
    return appt


# ── Validation errors ────────────────────────────────────────────────────────


@pytest.mark.integration
class TestCommitValidation:
    def test_empty_cart_returns_200_with_error(self, client, booking_settings):
        _store_cart(client, PublicCart())
        resp = client.post(reverse("booking:commit"), _valid_contact())
        assert resp.status_code == 200

    def test_missing_name_returns_error(self, client, service, booking_settings):
        cart = _cart_with_slot(service)
        _store_cart(client, cart)
        data = {**_valid_contact(), "first_name": "", "last_name": ""}
        resp = client.post(reverse("booking:commit"), data)
        assert resp.status_code == 200

    def test_missing_phone_and_email_returns_error(self, client, service, booking_settings):
        cart = _cart_with_slot(service)
        _store_cart(client, cart)
        data = {**_valid_contact(), "phone": "", "email": ""}
        resp = client.post(reverse("booking:commit"), data)
        assert resp.status_code == 200

    def test_missing_cancellation_policy_returns_error(self, client, service, booking_settings):
        cart = _cart_with_slot(service)
        _store_cart(client, cart)
        data = {**_valid_contact(), "cancellation_policy": ""}
        resp = client.post(reverse("booking:commit"), data)
        assert resp.status_code == 200

    def test_missing_consent_returns_error(self, client, service, booking_settings):
        cart = _cart_with_slot(service)
        _store_cart(client, cart)
        data = {**_valid_contact(), "consent": ""}
        resp = client.post(reverse("booking:commit"), data)
        assert resp.status_code == 200

    def test_no_slot_selected_returns_error(self, client, service, booking_settings):
        # Cart with no date/time
        cart = PublicCart(mode=MODE_SAME_DAY, stage=3)
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)
        resp = client.post(reverse("booking:commit"), _valid_contact())
        assert resp.status_code == 200


# ── Successful same-day commit ────────────────────────────────────────────────


@pytest.mark.integration
class TestCommitSameDay:
    def test_single_service_redirects_to_success_single(self, client, master, service, booking_settings):
        cart = _cart_with_slot(service)
        _store_cart(client, cart)

        appt = _mock_appointment("SINGLETOKEN")

        with (
            patch("features.booking.views.public.commit.get_booking_engine_gateway") as mock_gw,
            patch("features.conversations.services.notifications._get_engine") as mock_eng,
        ):
            mock_gw.return_value.create_booking.return_value = appt
            mock_eng.return_value = MagicMock()

            resp = client.post(reverse("booking:commit"), _valid_contact())

        assert resp.status_code == 200
        assert resp.headers.get("HX-Redirect", "").endswith(
            reverse("booking:success_single", kwargs={"token": "SINGLETOKEN"})
        )

    def test_multi_service_same_day_redirects_to_success_group(self, client, master, service, booking_settings):
        from tests.factories import AppointmentFactory, ServiceFactory

        service.masters.add(master)
        svc2 = ServiceFactory()
        svc2.masters.add(master)

        cart = PublicCart(mode=MODE_SAME_DAY, stage=3, date="2026-06-15", time="10:00")
        for svc in (service, svc2):
            cart.add(
                PublicCartItem(
                    service_id=svc.pk,
                    service_title=svc.name,
                    duration=svc.duration,
                    price=svc.price,
                )
            )
        _store_cart(client, cart)

        # Use real DB-backed appointments so AppointmentGroupItem FK works
        appt1 = AppointmentFactory(master=master, service=service, status="pending")
        appt2 = AppointmentFactory(master=master, service=svc2, status="pending")

        with (
            patch("features.booking.views.public.commit.get_booking_engine_gateway") as mock_gw,
            patch("features.conversations.services.notifications._get_engine") as mock_eng,
        ):
            mock_gw.return_value.create_booking.return_value = [appt1, appt2]
            mock_eng.return_value = MagicMock()

            resp = client.post(reverse("booking:commit"), _valid_contact())

        assert resp.status_code == 200
        hx_redirect = resp.headers.get("HX-Redirect", "")
        assert "success/group/" in hx_redirect

    def test_booking_exception_returns_error(self, client, service, booking_settings):
        cart = _cart_with_slot(service)
        _store_cart(client, cart)

        with patch("features.booking.views.public.commit.get_booking_engine_gateway") as mock_gw:
            mock_gw.return_value.create_booking.side_effect = RuntimeError("DB down")
            resp = client.post(reverse("booking:commit"), _valid_contact())

        assert resp.status_code == 200  # renders error template

    def test_cart_is_cleared_after_successful_commit(self, client, service, booking_settings):
        cart = _cart_with_slot(service)
        _store_cart(client, cart)

        appt = _mock_appointment("CLEARTOKEN")

        with (
            patch("features.booking.views.public.commit.get_booking_engine_gateway") as mock_gw,
            patch("features.conversations.services.notifications._get_engine") as mock_eng,
        ):
            mock_gw.return_value.create_booking.return_value = appt
            mock_eng.return_value = MagicMock()
            client.post(reverse("booking:commit"), _valid_contact())

        assert SESSION_KEY not in client.session


# ── Successful multi-day commit ───────────────────────────────────────────────


@pytest.mark.integration
class TestCommitMultiDay:
    def test_multi_day_redirects_to_success_multi(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_MULTI_DAY, stage=3)
        item = PublicCartItem(
            service_id=service.pk,
            service_title=service.name,
            duration=service.duration,
            price=service.price,
        )
        item.date = "2026-06-15"
        item.time = "10:00"
        cart.add(item)
        _store_cart(client, cart)

        appt = _mock_appointment("MULTITOKEN")

        with (
            patch("features.booking.views.public.commit.get_booking_engine_gateway") as mock_gw,
            patch("features.conversations.services.notifications._get_engine") as mock_eng,
        ):
            mock_gw.return_value.create_booking.return_value = appt
            mock_eng.return_value = MagicMock()
            resp = client.post(reverse("booking:commit"), _valid_contact())

        assert resp.status_code == 200
        hx_redirect = resp.headers.get("HX-Redirect", "")
        assert "success/multi/" in hx_redirect
        assert "MULTITOKEN" in hx_redirect


# ── Success pages ─────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestSuccessPages:
    def test_success_single_renders(self, client, pending_appointment):
        pending_appointment.finalize_token = "FINTOKEN"
        pending_appointment.save()

        url = reverse("booking:success_single", kwargs={"token": "FINTOKEN"})
        resp = client.get(url)
        assert resp.status_code == 200

    def test_success_single_404_on_bad_token(self, client):
        url = reverse("booking:success_single", kwargs={"token": "BADTOKEN"})
        resp = client.get(url)
        assert resp.status_code == 404

    def test_success_multi_view_renders(self, db, pending_appointment, rf):
        """Test BookingSuccessMultiView directly (bypasses URL routing bug where
        success/<str:token>/ shadows success/multi/).
        See spawn_task: Fix URL ordering: success_multi shadowed by success_single.
        """
        from django.contrib.auth.models import AnonymousUser
        from features.booking.views.public.commit import BookingSuccessMultiView

        pending_appointment.finalize_token = "MULTIOK"
        pending_appointment.save()

        request = rf.get("/fake/", {"tokens": "MULTIOK"})
        request.session = {}
        request.user = AnonymousUser()
        view = BookingSuccessMultiView.as_view()
        resp = view(request)
        assert resp.status_code == 200

    def test_success_multi_view_renders_empty_tokens(self, db, rf):
        from django.contrib.auth.models import AnonymousUser
        from features.booking.views.public.commit import BookingSuccessMultiView

        request = rf.get("/fake/", {"tokens": ""})
        request.session = {}
        request.user = AnonymousUser()
        view = BookingSuccessMultiView.as_view()
        resp = view(request)
        assert resp.status_code == 200


# ── _get_or_create_client utility ─────────────────────────────────────────────


@pytest.mark.integration
class TestGetOrCreateClient:
    def test_creates_new_client(self, db):
        from features.booking.views.public.commit import _get_or_create_client

        client = _get_or_create_client("Max", "Mustermann", "+49111222333", "")
        assert client.pk is not None
        assert client.first_name == "Max"

    def test_finds_existing_by_phone(self, db, client_obj):
        from features.booking.views.public.commit import _get_or_create_client

        result = _get_or_create_client("X", "Y", client_obj.phone, "")
        assert result.pk == client_obj.pk

    def test_finds_existing_by_email_when_no_phone(self, db, client_obj):
        from features.booking.views.public.commit import _get_or_create_client

        result = _get_or_create_client("X", "Y", "", client_obj.email)
        assert result.pk == client_obj.pk
