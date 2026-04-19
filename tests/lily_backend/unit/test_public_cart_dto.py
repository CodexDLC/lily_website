"""Unit tests for features/booking/dto/public_cart.py — pure dataclass logic, no I/O."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from features.booking.dto.public_cart import (
    MODE_MULTI_DAY,
    MODE_SAME_DAY,
    SESSION_KEY,
    PublicCart,
    PublicCartItem,
    clear_cart,
    get_cart,
    save_cart,
)


def _item(service_id: int = 1, price: str = "50.00", duration: int = 60) -> PublicCartItem:
    return PublicCartItem(
        service_id=service_id,
        service_title=f"Service {service_id}",
        duration=duration,
        price=Decimal(price),
    )


# ── PublicCartItem ────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestPublicCartItem:
    def test_to_dict_roundtrip(self):
        item = _item(1, "75.50", 90)
        item.date = "2026-05-10"
        item.time = "11:00"
        d = item.to_dict()
        restored = PublicCartItem.from_dict(d)
        assert restored.service_id == 1
        assert restored.price == Decimal("75.50")
        assert restored.duration == 90
        assert restored.date == "2026-05-10"
        assert restored.time == "11:00"

    def test_from_dict_missing_optional_fields(self):
        d = {
            "service_id": 2,
            "service_title": "X",
            "duration": 30,
            "price": "20.00",
        }
        item = PublicCartItem.from_dict(d)
        assert item.date is None
        assert item.time is None


# ── PublicCart operations ─────────────────────────────────────────────────────


@pytest.mark.unit
class TestPublicCart:
    def test_add_unique_only(self):
        cart = PublicCart()
        cart.add(_item(1))
        cart.add(_item(1))  # duplicate — should not add
        assert len(cart.items) == 1

    def test_add_multiple_different(self):
        cart = PublicCart()
        cart.add(_item(1))
        cart.add(_item(2))
        assert len(cart.items) == 2

    def test_remove(self):
        cart = PublicCart()
        cart.add(_item(1))
        cart.add(_item(2))
        cart.remove(1)
        assert not cart.has(1)
        assert cart.has(2)

    def test_remove_ids_bulk(self):
        cart = PublicCart()
        for i in range(1, 5):
            cart.add(_item(i))
        cart.remove_ids([1, 3])
        assert cart.service_ids() == [2, 4]

    def test_has(self):
        cart = PublicCart()
        cart.add(_item(7))
        assert cart.has(7)
        assert not cart.has(8)

    def test_is_empty(self):
        cart = PublicCart()
        assert cart.is_empty()
        cart.add(_item(1))
        assert not cart.is_empty()

    def test_service_ids(self):
        cart = PublicCart()
        cart.add(_item(3))
        cart.add(_item(5))
        assert cart.service_ids() == [3, 5]

    def test_total_price(self):
        cart = PublicCart()
        cart.add(_item(1, "30.00"))
        cart.add(_item(2, "20.50"))
        assert cart.total_price() == Decimal("50.50")

    def test_total_price_empty(self):
        cart = PublicCart()
        assert cart.total_price() == Decimal("0")

    def test_total_duration(self):
        cart = PublicCart()
        cart.add(_item(1, duration=60))
        cart.add(_item(2, duration=45))
        assert cart.total_duration() == 105

    def test_set_item_slot(self):
        cart = PublicCart()
        cart.add(_item(1))
        cart.set_item_slot(1, "2026-05-10", "14:30")
        assert cart.items[0].date == "2026-05-10"
        assert cart.items[0].time == "14:30"

    def test_set_item_slot_wrong_id_noop(self):
        cart = PublicCart()
        cart.add(_item(1))
        cart.set_item_slot(99, "2026-05-10", "14:30")
        assert cart.items[0].date is None

    # ── Readiness checks ─────────────────────────────────────────────────────

    def test_is_ready_same_day_true(self):
        cart = PublicCart()
        cart.add(_item(1))
        cart.date = "2026-05-10"
        cart.time = "10:00"
        assert cart.is_ready_same_day()

    def test_is_ready_same_day_missing_time(self):
        cart = PublicCart()
        cart.add(_item(1))
        cart.date = "2026-05-10"
        assert not cart.is_ready_same_day()

    def test_is_ready_same_day_empty_cart(self):
        cart = PublicCart(date="2026-05-10", time="10:00")
        assert not cart.is_ready_same_day()

    def test_is_ready_multi_day_true(self):
        cart = PublicCart(mode=MODE_MULTI_DAY)
        cart.add(_item(1))
        cart.add(_item(2))
        cart.set_item_slot(1, "2026-05-10", "10:00")
        cart.set_item_slot(2, "2026-05-11", "11:00")
        assert cart.is_ready_multi_day()

    def test_is_ready_multi_day_partial(self):
        cart = PublicCart(mode=MODE_MULTI_DAY)
        cart.add(_item(1))
        cart.add(_item(2))
        cart.set_item_slot(1, "2026-05-10", "10:00")
        # item 2 has no slot
        assert not cart.is_ready_multi_day()

    def test_is_group_booking_same_day_two_items(self):
        cart = PublicCart(mode=MODE_SAME_DAY)
        cart.add(_item(1))
        cart.add(_item(2))
        assert cart.is_group_booking()

    def test_is_group_booking_same_day_one_item(self):
        cart = PublicCart(mode=MODE_SAME_DAY)
        cart.add(_item(1))
        assert not cart.is_group_booking()

    def test_is_group_booking_multi_day_not_group(self):
        cart = PublicCart(mode=MODE_MULTI_DAY)
        cart.add(_item(1))
        cart.add(_item(2))
        assert not cart.is_group_booking()

    # ── Serialisation ─────────────────────────────────────────────────────────

    def test_to_dict_from_dict_roundtrip(self):
        cart = PublicCart(mode=MODE_SAME_DAY, stage=2, date="2026-05-10", time="10:00")
        cart.add(_item(1, "50.00", 60))
        cart.contact = {"name": "Anna", "phone": "+49111", "email": "a@a.com"}
        d = cart.to_dict()
        restored = PublicCart.from_dict(d)
        assert restored.mode == MODE_SAME_DAY
        assert restored.stage == 2
        assert restored.date == "2026-05-10"
        assert restored.time == "10:00"
        assert len(restored.items) == 1
        assert restored.items[0].service_id == 1
        assert restored.contact["name"] == "Anna"

    def test_from_dict_defaults(self):
        cart = PublicCart.from_dict({})
        assert cart.mode == MODE_SAME_DAY
        assert cart.stage == 1
        assert cart.items == []
        assert cart.date is None
        assert cart.time is None


# ── Session helpers ───────────────────────────────────────────────────────────


class _FakeSession(dict):
    """Minimal session mock that supports the `modified` attribute."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = False


@pytest.mark.unit
class TestCartSessionHelpers:
    def _mock_request(self, session_data: dict | None = None) -> MagicMock:
        req = MagicMock()
        req.session = _FakeSession()
        if session_data is not None:
            req.session[SESSION_KEY] = session_data
        return req

    def test_get_cart_empty_session(self):
        req = self._mock_request()
        cart = get_cart(req)
        assert cart.is_empty()
        assert cart.mode == MODE_SAME_DAY

    def test_get_cart_from_session(self):
        item = _item(3, "100.00", 120)
        existing = PublicCart()
        existing.add(item)
        req = self._mock_request(existing.to_dict())
        cart = get_cart(req)
        assert cart.has(3)

    def test_save_cart(self):
        req = self._mock_request()
        cart = PublicCart()
        cart.add(_item(5))
        save_cart(req, cart)
        assert SESSION_KEY in req.session
        assert req.session.modified is True

    def test_clear_cart(self):
        req = self._mock_request({"items": []})
        clear_cart(req)
        assert SESSION_KEY not in req.session
        assert req.session.modified is True

    def test_clear_cart_noop_if_missing(self):
        req = self._mock_request()
        clear_cart(req)  # should not raise
        assert req.session.modified is True
