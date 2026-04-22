"""Integration tests for public booking cart views (CartAddView, CartRemoveView,
CartSetModeView, CartSetStageView).

Uses sqlite in-memory + Django test client. Templates are rendered so we catch
any context/template errors.
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


# ── CartAddView ───────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestCartAddView:
    def test_missing_service_id_returns_400(self, client):
        url = reverse("booking:cart_add")
        resp = client.post(url, {})
        assert resp.status_code == 400

    def test_invalid_service_id_returns_404(self, client):
        url = reverse("booking:cart_add")
        resp = client.post(url, {"service_id": "99999"})
        assert resp.status_code == 404

    def test_add_service_persists_to_session(self, client, master, service, booking_settings):
        service.masters.add(master)
        url = reverse("booking:cart_add")
        resp = client.post(url, {"service_id": str(service.pk)})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.has(service.pk)

    def test_add_service_returns_booking_hub_summary(self, client, master, service, booking_settings):
        service.masters.add(master)

        resp = client.post(reverse("booking:cart_add"), {"service_id": str(service.pk)})

        assert resp.status_code == 200
        content = resp.content.decode()
        assert "bk-hub-panel" in content
        assert "Selected" in content
        assert "(1)" in content
        assert "60 min" in content
        assert "50.00 €" in content

    def test_add_duplicate_service_is_idempotent(self, client, master, service, booking_settings):
        service.masters.add(master)
        cart = PublicCart()
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)

        url = reverse("booking:cart_add")
        resp = client.post(url, {"service_id": str(service.pk)})
        assert resp.status_code == 200
        # Still only one item
        cart = _read_cart(client)
        assert len(cart.items) == 1

    def test_add_service_resets_slot(self, client, master, service, booking_settings):
        service.masters.add(master)
        cart = PublicCart(date="2026-05-10", time="10:00")
        _store_cart(client, cart)

        url = reverse("booking:cart_add")
        client.post(url, {"service_id": str(service.pk)})
        cart = _read_cart(client)
        assert cart.date is None
        assert cart.time is None

    def test_excludes_conflict_returns_error_html(self, client, master, service, booking_settings):
        from features.main.models import Service, ServiceCategory, ServiceConflictRule

        service.masters.add(master)
        cat2 = ServiceCategory.objects.create(name="Cat2", slug="cat2", bento_group="nails")
        conflicting = Service.objects.create(
            category=cat2,
            name="Conflicting",
            slug="conflicting-svc",
            price="30.00",
            duration=30,
            is_active=True,
        )
        conflicting.masters.add(master)

        # Add conflicting service first
        cart = PublicCart()
        cart.add(
            PublicCartItem(
                service_id=conflicting.pk,
                service_title=conflicting.name,
                duration=conflicting.duration,
                price=conflicting.price,
            )
        )
        _store_cart(client, cart)

        # Create EXCLUDES rule: service EXCLUDES conflicting
        ServiceConflictRule.objects.create(
            source=service,
            target=conflicting,
            rule_type=ServiceConflictRule.EXCLUDES,
            is_active=True,
        )

        url = reverse("booking:cart_add")
        resp = client.post(url, {"service_id": str(service.pk)})
        assert resp.status_code == 200
        # Cart should still have conflicting, not the new service
        cart = _read_cart(client)
        assert not cart.has(service.pk)

    def test_replaces_conflict_removes_old(self, client, master, service, booking_settings):
        from features.main.models import Service, ServiceCategory, ServiceConflictRule

        service.masters.add(master)
        cat2 = ServiceCategory.objects.create(name="CatR", slug="cat-r", bento_group="nails")
        old_svc = Service.objects.create(
            category=cat2,
            name="Old Service",
            slug="old-svc",
            price="20.00",
            duration=30,
            is_active=True,
        )
        old_svc.masters.add(master)

        cart = PublicCart()
        cart.add(
            PublicCartItem(
                service_id=old_svc.pk,
                service_title=old_svc.name,
                duration=old_svc.duration,
                price=old_svc.price,
            )
        )
        _store_cart(client, cart)

        # REPLACES rule: service replaces old_svc
        ServiceConflictRule.objects.create(
            source=service,
            target=old_svc,
            rule_type=ServiceConflictRule.REPLACES,
            is_active=True,
        )

        url = reverse("booking:cart_add")
        resp = client.post(url, {"service_id": str(service.pk)})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.has(service.pk)
        assert not cart.has(old_svc.pk)


# ── CartRemoveView ────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestCartRemoveView:
    def test_missing_service_id_returns_400(self, client):
        resp = client.post(reverse("booking:cart_remove"), {})
        assert resp.status_code == 400

    def test_removes_service_from_session(self, client, service):
        cart = PublicCart()
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)

        resp = client.post(reverse("booking:cart_remove"), {"service_id": str(service.pk)})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert not cart.has(service.pk)

    def test_remove_from_hub_updates_hub_and_service_button(self, client, service, category):
        from features.main.models import Service

        keep_service = Service.objects.create(
            category=category,
            name="Keep Service",
            slug="keep-svc",
            price="20.00",
            duration=30,
            is_active=True,
        )
        cart = PublicCart()
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        cart.add(
            PublicCartItem(
                service_id=keep_service.pk,
                service_title=keep_service.name,
                duration=keep_service.duration,
                price=keep_service.price,
            )
        )
        _store_cart(client, cart)

        resp = client.post(reverse("booking:cart_remove"), {"service_id": str(service.pk), "source": "hub"})

        assert resp.status_code == 200
        content = resp.content.decode()
        assert "bk-hub-panel" in content
        assert "Keep Service" in content
        assert "Test Service" not in content
        assert f'id="service-action-{service.pk}"' in content
        assert "hx-swap-oob" in content
        cart = _read_cart(client)
        assert not cart.has(service.pk)
        assert cart.has(keep_service.pk)

    def test_remove_last_item_from_hub_returns_empty_hub(self, client, service):
        cart = PublicCart()
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)

        resp = client.post(reverse("booking:cart_remove"), {"service_id": str(service.pk), "source": "hub"})

        assert resp.status_code == 200
        content = resp.content.decode()
        assert '<div id="bk-hub"></div>' in content
        assert "bk-hub-panel" not in content
        assert f'id="service-action-{service.pk}"' in content
        cart = _read_cart(client)
        assert cart.is_empty()

    def test_remove_resets_slot(self, client, service):
        cart = PublicCart(date="2026-05-10", time="10:00")
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)

        client.post(reverse("booking:cart_remove"), {"service_id": str(service.pk)})
        cart = _read_cart(client)
        assert cart.date is None


# ── CartSetModeView ────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestCartSetModeView:
    def test_set_mode_same_day(self, client, service):
        cart = PublicCart(mode=MODE_MULTI_DAY)
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)

        resp = client.post(reverse("booking:cart_set_mode"), {"mode": "same_day"})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.mode == MODE_SAME_DAY

    def test_set_mode_multi_day(self, client, service):
        cart = PublicCart(mode=MODE_SAME_DAY)
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)

        resp = client.post(reverse("booking:cart_set_mode"), {"mode": "multi_day"})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.mode == MODE_MULTI_DAY

    def test_invalid_mode_defaults_to_same_day(self, client):
        resp = client.post(reverse("booking:cart_set_mode"), {"mode": "invalid"})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.mode == MODE_SAME_DAY

    def test_mode_switch_resets_slots(self, client, service):
        cart = PublicCart(mode=MODE_SAME_DAY, date="2026-05-10", time="10:00")
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        cart.items[0].date = "2026-05-10"
        cart.items[0].time = "10:00"
        _store_cart(client, cart)

        client.post(reverse("booking:cart_set_mode"), {"mode": "multi_day"})
        cart = _read_cart(client)
        assert cart.date is None
        assert cart.items[0].date is None


# ── CartSetStageView ──────────────────────────────────────────────────────────


@pytest.mark.integration
class TestCartSetStageView:
    def test_set_stage_1(self, client, service):
        cart = PublicCart(stage=2)
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)

        resp = client.post(reverse("booking:cart_set_stage"), {"stage": "1"})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.stage == 1

    def test_set_stage_invalid_defaults_to_1(self, client):
        resp = client.post(reverse("booking:cart_set_stage"), {"stage": "bad"})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.stage == 1

    def test_set_stage_3_with_items(self, client, service):
        cart = PublicCart(stage=2)
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        _store_cart(client, cart)

        resp = client.post(reverse("booking:cart_set_stage"), {"stage": "3"})
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.stage == 3
