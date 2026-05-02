"""Public booking wizard — shell page."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import render
from django.views import View

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

from features.booking.dto.public_cart import PublicCartItem, get_cart, save_cart
from features.booking.providers import get_booking_project_data_provider
from features.main.models import ServiceCombo


class BookingWizardView(View):
    """Shell page for the public booking wizard.

    Supports pre-filling cart via query params:
        ?service=<slug>           — pre-add single service
        ?services=<slug>,<slug>   — pre-add multiple services
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        cart = get_cart(request)
        provider = get_booking_project_data_provider()
        services = provider.get_public_services()

        # Build slug → service dict for pre-fill lookup
        service_by_slug = {s["slug"]: s for s in services}

        changed = False
        combo_slug = request.GET.get("combo", "").strip()
        if combo_slug:
            combo = (
                ServiceCombo.objects.filter(slug=combo_slug, is_active=True).prefetch_related("items__service").first()
            )
            if combo and combo.is_available_now:
                cart.items = []
                cart.clear_combo()
                cart.date = None
                cart.time = None
                cart.stage = 1

                for combo_item in combo.items.all():
                    service = combo_item.service
                    if service.is_active:
                        cart.add(
                            PublicCartItem(
                                service_id=service.pk,
                                service_title=service.name,
                                duration=service.duration,
                                price=service.price,
                            )
                        )

                if cart.items and combo.discount_type == ServiceCombo.FIXED_PRICE:
                    cart.apply_combo(
                        combo_id=combo.pk,
                        combo_slug=combo.slug,
                        combo_title=combo.name,
                        combo_price=combo.discount_value,
                    )
                changed = True

        slugs_raw = "" if combo_slug else request.GET.get("services") or request.GET.get("service") or ""
        for slug in slugs_raw.split(","):
            slug = slug.strip()
            if slug and slug in service_by_slug:
                s = service_by_slug[slug]
                from decimal import Decimal

                if not cart.has(s["id"]):
                    cart.add(
                        PublicCartItem(
                            service_id=s["id"],
                            service_title=s["title"],
                            duration=s["duration"],
                            price=Decimal(s["price"]),
                        )
                    )
                    changed = True

        if changed:
            save_cart(request, cart)

        # Group services by category for the service selector UI
        categories: dict[str, dict] = {}
        for s in services:
            cat_slug = s["category_slug"]
            if cat_slug not in categories:
                categories[cat_slug] = {
                    "slug": cat_slug,
                    "name": s["category_name"],
                    "services": [],
                }
            categories[cat_slug]["services"].append(s)

        return render(
            request,
            "features/booking/wizard.html",
            {
                "cart": cart,
                "cart_ids": set(cart.service_ids()),
                "categories": list(categories.values()),
                "services_json": services,
            },
        )
