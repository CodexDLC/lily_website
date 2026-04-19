"""Integration tests for SchedulerConfirmTimeView (POST).

Uses sqlite in-memory + Django test client. Covers same-day and multi-day slot
confirmation flows, and error cases (missing service_id, bad date).
"""

from __future__ import annotations

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


def _read_cart(client) -> PublicCart:
    return PublicCart.from_dict(client.session.get(SESSION_KEY, {}))


def _item(service) -> PublicCartItem:
    return PublicCartItem(
        service_id=service.pk,
        service_title=service.name,
        duration=service.duration,
        price=service.price,
    )


URL = "booking:scheduler_confirm_time"


@pytest.mark.integration
class TestSchedulerConfirmTimeSameDay:
    def test_same_day_sets_date_time_and_stage_3(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_SAME_DAY, stage=2)
        cart.add(_item(service))
        _store_cart(client, cart)

        resp = client.post(reverse(URL), {"date": "2026-06-15", "time": "11:00"})
        assert resp.status_code == 200

        cart = _read_cart(client)
        assert cart.date == "2026-06-15"
        assert cart.time == "11:00"
        assert cart.stage == 3

    def test_same_day_response_contains_sidebar_oob(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_SAME_DAY, stage=2)
        cart.add(_item(service))
        _store_cart(client, cart)

        resp = client.post(reverse(URL), {"date": "2026-06-15", "time": "14:30"})
        content = resp.content.decode()
        assert "bk-sidebar-wrapper" in content

    def test_same_day_empty_time_still_persists(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_SAME_DAY, stage=2)
        cart.add(_item(service))
        _store_cart(client, cart)

        resp = client.post(reverse(URL), {"date": "2026-06-15", "time": ""})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.time == ""
        assert cart.stage == 3


@pytest.mark.integration
class TestSchedulerConfirmTimeMultiDay:
    def test_multi_day_sets_item_slot(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_MULTI_DAY, stage=2)
        cart.add(_item(service))
        _store_cart(client, cart)

        resp = client.post(
            reverse(URL),
            {"date": "2026-06-15", "time": "10:00", "service_id": str(service.pk)},
        )
        assert resp.status_code == 200

        cart = _read_cart(client)
        item = next(i for i in cart.items if i.service_id == service.pk)
        assert item.date == "2026-06-15"
        assert item.time == "10:00"

    def test_multi_day_missing_service_id_returns_400(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_MULTI_DAY, stage=2)
        cart.add(_item(service))
        _store_cart(client, cart)

        resp = client.post(
            reverse(URL),
            {"date": "2026-06-15", "time": "10:00"},  # no service_id
        )
        assert resp.status_code == 400

    def test_multi_day_bad_date_returns_400(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_MULTI_DAY, stage=2)
        cart.add(_item(service))
        _store_cart(client, cart)

        resp = client.post(
            reverse(URL),
            {"date": "not-a-date", "time": "10:00", "service_id": str(service.pk)},
        )
        assert resp.status_code == 400

    def test_multi_day_non_integer_service_id_returns_400(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_MULTI_DAY, stage=2)
        cart.add(_item(service))
        _store_cart(client, cart)

        resp = client.post(
            reverse(URL),
            {"date": "2026-06-15", "time": "10:00", "service_id": "bad"},
        )
        assert resp.status_code == 400

    def test_multi_day_response_renders_scheduler_panel(self, client, service, booking_settings):
        cart = PublicCart(mode=MODE_MULTI_DAY, stage=2)
        cart.add(_item(service))
        _store_cart(client, cart)

        resp = client.post(
            reverse(URL),
            {"date": "2026-06-15", "time": "10:00", "service_id": str(service.pk)},
        )
        assert resp.status_code == 200
        # Response renders scheduler_panel partial (not the full-page OOB multi-response)
        assert b"bk-sidebar-wrapper" not in resp.content
