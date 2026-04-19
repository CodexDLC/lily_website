"""Integration tests for BookingWizardView (GET).

Covers the public booking wizard shell page including:
- Basic render (no params)
- Pre-fill via ?service=<slug> and ?services=<slug>,<slug> query params
- Cart persistence when service pre-filled
- Duplicate slug handling (idempotent)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from features.booking.dto.public_cart import SESSION_KEY, PublicCart


def _read_cart(client) -> PublicCart:
    return PublicCart.from_dict(client.session.get(SESSION_KEY, {}))


@pytest.mark.integration
class TestBookingWizardView:
    def test_get_renders_200(self, client, master, service, booking_settings):
        service.masters.add(master)
        resp = client.get(reverse("booking:booking_wizard"))
        assert resp.status_code == 200

    def test_get_includes_categories_context(self, client, master, service, booking_settings):
        service.masters.add(master)
        resp = client.get(reverse("booking:booking_wizard"))
        assert "categories" in resp.context
        assert "cart" in resp.context

    def test_get_no_params_does_not_modify_cart(self, client, master, service, booking_settings):
        service.masters.add(master)
        client.get(reverse("booking:booking_wizard"))
        cart = _read_cart(client)
        assert cart.is_empty()

    def test_service_param_prefills_cart(self, client, master, service, booking_settings):
        service.masters.add(master)
        resp = client.get(reverse("booking:booking_wizard") + f"?service={service.slug}")
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.has(service.pk)

    def test_services_param_prefills_multiple(self, client, master, service, booking_settings):
        from tests.factories import ServiceFactory

        service.masters.add(master)
        svc2 = ServiceFactory()
        svc2.masters.add(master)

        resp = client.get(reverse("booking:booking_wizard") + f"?services={service.slug},{svc2.slug}")
        assert resp.status_code == 200
        cart = _read_cart(client)
        assert cart.has(service.pk)
        assert cart.has(svc2.pk)

    def test_unknown_slug_is_ignored(self, client, master, service, booking_settings):
        service.masters.add(master)
        client.get(reverse("booking:booking_wizard") + "?service=nonexistent-slug")
        cart = _read_cart(client)
        assert cart.is_empty()

    def test_service_param_is_idempotent(self, client, master, service, booking_settings):
        service.masters.add(master)
        client.get(reverse("booking:booking_wizard") + f"?service={service.slug}")
        client.get(reverse("booking:booking_wizard") + f"?service={service.slug}")
        cart = _read_cart(client)
        assert len(cart.items) == 1
