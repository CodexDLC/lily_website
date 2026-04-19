"""Cart HTMX views — add, remove, set mode."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views import View

from features.booking.dto.public_cart import (
    PublicCartItem,
    get_cart,
    save_cart,
)
from features.main.models import Service, ServiceConflictRule


def _get_categories():
    from features.booking.providers import get_booking_project_data_provider

    provider = get_booking_project_data_provider()
    services = provider.get_public_services()
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
    return list(categories.values())


def _render_cart(request: HttpRequest, cart, *, error: str = "") -> HttpResponse:
    return render(
        request,
        "features/booking/partials/cart_panel.html",
        {
            "cart": cart,
            "cart_ids": set(cart.service_ids()),
            "error": error,
            "categories": _get_categories(),
        },
    )


class CartAddView(View):
    """POST service_id → add to cart, apply conflict rules, return cart panel."""

    def post(self, request: HttpRequest) -> HttpResponse:
        service_id = request.POST.get("service_id")
        if not service_id:
            return HttpResponse(status=400)

        try:
            service = Service.objects.select_related("category").get(pk=int(service_id), is_active=True)
        except (Service.DoesNotExist, ValueError):
            return HttpResponse(status=404)

        cart = get_cart(request)

        if cart.has(service.pk):
            return _render_cart(request, cart)

        # Apply conflict rules (server-side, source → this service)
        rules = ServiceConflictRule.objects.filter(source=service, is_active=True).select_related("target")

        ids_to_remove: list[int] = []
        for rule in rules:
            if cart.has(rule.target_id):
                if rule.rule_type == ServiceConflictRule.REPLACES:
                    ids_to_remove.append(rule.target_id)
                elif rule.rule_type == ServiceConflictRule.EXCLUDES:
                    return _render_cart(
                        request,
                        cart,
                        error=_(
                            "Die Dienstleistung «%(service)s» ist nicht kompatibel mit den bereits ausgewählten Leistungen."
                        )
                        % {"service": service.name},
                    )

        # Also check reverse excludes (B excludes A even if rule is on target side)
        reverse_excludes = ServiceConflictRule.objects.filter(
            target=service, rule_type=ServiceConflictRule.EXCLUDES, is_active=True
        ).values_list("source_id", flat=True)
        for src_id in reverse_excludes:
            if cart.has(src_id):
                return _render_cart(
                    request,
                    cart,
                    error=_(
                        "Die Dienstleistung «%(service)s» ist nicht kompatibel mit den bereits ausgewählten Leistungen."
                    )
                    % {"service": service.name},
                )

        cart.remove_ids(ids_to_remove)
        cart.add(
            PublicCartItem(
                service_id=service.pk,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        )
        # Adding a service resets previously selected slot
        cart.date = None
        cart.time = None
        for item in cart.items:
            item.date = None
            item.time = None

        save_cart(request, cart)

        # Handle in-place button toggle plus hub refresh
        button_html = render(
            request, "features/booking/partials/bookable_button.html", {"service_id": service.id, "is_selected": True}
        ).content.decode("utf-8")

        hub_html = render(
            request, "features/booking/partials/booking_hub.html", {"cart": cart, "cart_ids": set(cart.service_ids())}
        ).content.decode("utf-8")

        # OOB update for hub, direct swap for button
        response_html = f'{button_html}<div id="bk-hub-placeholder" hx-swap-oob="innerHTML">{hub_html}</div>'

        # If conflicts occurred, we need to refresh those buttons too OOB
        for removed_id in ids_to_remove:
            conflict_btn = render(
                request,
                "features/booking/partials/bookable_button.html",
                {"service_id": removed_id, "is_selected": False},
            ).content.decode("utf-8")
            response_html += f'<div id="service-action-{removed_id}" hx-swap-oob="innerHTML">{conflict_btn}</div>'

        return HttpResponse(response_html)


class CartRemoveView(View):
    """POST service_id → remove from cart, return toggled button + hub."""

    def post(self, request: HttpRequest) -> HttpResponse:
        service_id = request.POST.get("service_id")
        if not service_id:
            return HttpResponse(status=400)

        cart = get_cart(request)
        cart.remove(int(service_id))
        cart.date = None
        cart.time = None
        for item in cart.items:
            item.date = None
            item.time = None

        save_cart(request, cart)

        button_html = render(
            request, "features/booking/partials/bookable_button.html", {"service_id": service_id, "is_selected": False}
        ).content.decode("utf-8")

        hub_html = render(
            request, "features/booking/partials/booking_hub.html", {"cart": cart, "cart_ids": set(cart.service_ids())}
        ).content.decode("utf-8")

        response_html = f'{button_html}<div id="bk-hub-placeholder" hx-swap-oob="innerHTML">{hub_html}</div>'
        return HttpResponse(response_html)


class CartSetModeView(View):
    """POST mode=same_day|multi_day → switch booking mode, return scheduler panel."""

    def post(self, request: HttpRequest) -> HttpResponse:
        mode = request.POST.get("mode", "same_day")
        if mode not in ("same_day", "multi_day"):
            mode = "same_day"

        cart = get_cart(request)
        cart.mode = mode
        # Reset all slot selections on mode switch
        cart.date = None
        cart.time = None
        for item in cart.items:
            item.date = None
            item.time = None

        save_cart(request, cart)
        return render(
            request,
            "features/booking/partials/scheduler_panel.html",
            {"cart": cart},
        )


class CartSetStageView(View):
    """POST stage=1|2|3 → update wizard progress."""

    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            stage = int(request.POST.get("stage", 1))
        except ValueError:
            stage = 1

        cart = get_cart(request)
        cart.stage = stage
        save_cart(request, cart)

        # Re-render the relevant content for the wizard stage
        if stage == 1:
            template = "features/booking/partials/cart_panel.html"
        elif stage == 2:
            template = "features/booking/partials/scheduler_panel.html"
        else:
            template = "features/booking/partials/summary_panel.html"

        content_html = render(request, template, {"cart": cart}).content.decode("utf-8")

        # Add OOB updates for stepper and sidebar
        stepper_html = render(request, "features/booking/partials/stepper.html", {"cart": cart}).content.decode("utf-8")

        # Sidebar logic: Only show on stage 3 (Information)
        if not cart.is_empty and cart.stage == 3:
            sidebar_content = render(
                request, "features/booking/partials/summary_sidebar.html", {"cart": cart}
            ).content.decode("utf-8")
            sidebar_html = f'<div id="bk-sidebar-wrapper" hx-swap-oob="innerHTML"><aside class="wizard-sidebar">{sidebar_content}</aside></div>'
        else:
            sidebar_html = '<div id="bk-sidebar-wrapper" hx-swap-oob="innerHTML"></div>'

        # Toggle full-width class on the island
        is_full_width = "true" if cart.stage < 3 else "false"
        toggle_script = f'<script>document.getElementById("bk-wizard-island")?.classList.toggle("wizard-island--full-width", {is_full_width});</script>'

        return HttpResponse(content_html + stepper_html + sidebar_html + toggle_script)
