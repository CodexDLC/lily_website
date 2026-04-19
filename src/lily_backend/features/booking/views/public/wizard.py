"""Public booking wizard — shell page."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import render
from django.views import View

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

from features.booking.dto.public_cart import get_cart, save_cart
from features.booking.providers import get_booking_project_data_provider


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
        slugs_raw = request.GET.get("services") or request.GET.get("service") or ""
        for slug in slugs_raw.split(","):
            slug = slug.strip()
            if slug and slug in service_by_slug:
                s = service_by_slug[slug]
                from decimal import Decimal

                from features.booking.dto.public_cart import PublicCartItem

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
