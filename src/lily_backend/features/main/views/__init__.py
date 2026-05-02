from __future__ import annotations

from typing import Any

from django.db.models import Prefetch, Q
from django.http import Http404
from django.utils import timezone
from django.views.generic import TemplateView
from features.booking.models import Master
from features.booking.providers.runtime import RuntimeBookingProvider

from ..models import ServiceCategory, ServiceCombo


def get_featured_combos() -> Any:
    today = timezone.localdate()
    return (
        ServiceCombo.objects.filter(is_active=True, is_featured=True, show_on_home=True)
        .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=today))
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=today))
        .prefetch_related("items__service")
        .order_by("promo_order", "name")
    )


class HomeView(TemplateView):
    template_name = "features/main/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["combo_promos"] = get_featured_combos()
        ctx["bento"] = ServiceCategory.objects.filter(is_active=True).order_by("order", "name")
        ctx["team"] = Master.objects.filter(status=Master.STATUS_ACTIVE, is_public=True).order_by("order", "name")
        return ctx


class ServicesIndexView(TemplateView):
    template_name = "features/main/services/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from features.booking.dto.public_cart import get_cart

        ctx = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        cart_ids = set(cart.service_ids())
        provider = RuntimeBookingProvider()

        bookable_services = provider.get_bookable_services_queryset()

        # Pre-calculate selection for templates
        categories = (
            ServiceCategory.objects.filter(is_active=True)
            .filter(id__in=bookable_services.values("category_id"))
            .prefetch_related(
                Prefetch("services", queryset=bookable_services),
                "masters",
            )
            .distinct()
            .order_by("order")
        )
        for cat in categories:
            for svc in cat.services.all():
                svc.is_selected = svc.id in cart_ids

        ctx["categories"] = categories
        ctx["cart_ids"] = cart_ids
        ctx["cart"] = cart
        return ctx


class ServiceDetailView(TemplateView):
    template_name = "features/main/services/detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from features.booking.dto.public_cart import get_cart

        ctx = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug", "")
        provider = RuntimeBookingProvider()
        cart = get_cart(self.request)
        cart_ids = set(cart.service_ids())

        try:
            category = (
                ServiceCategory.objects.filter(is_active=True)
                .prefetch_related(
                    Prefetch("services", queryset=provider.get_bookable_services_queryset()),
                    Prefetch(
                        "masters",
                        queryset=Master.objects.filter(status=Master.STATUS_ACTIVE, is_public=True).order_by(
                            "order", "name"
                        ),
                    ),
                )
                .get(slug=slug)
            )
        except ServiceCategory.DoesNotExist:
            raise Http404 from None

        # Pre-calculate selection for templates
        for svc in category.services.all():
            svc.is_selected = svc.id in cart_ids

        ctx["category"] = category
        ctx["slug"] = slug
        ctx["cart"] = cart
        ctx["cart_ids"] = cart_ids
        ctx["other_categories"] = (
            ServiceCategory.objects.filter(is_active=True).exclude(id=category.id).order_by("?")[:6]
        )
        return ctx


class TeamView(TemplateView):
    template_name = "features/main/team.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        active_public = (
            Master.objects.filter(status=Master.STATUS_ACTIVE, is_public=True)
            .prefetch_related("categories")
            .order_by("order", "name")
        )

        ctx["owner"] = active_public.filter(is_owner=True).first()
        ctx["team"] = active_public.filter(is_owner=False)
        return ctx


class ImpressumView(TemplateView):
    template_name = "features/main/legal/impressum.html"


class DatenschutzView(TemplateView):
    template_name = "features/main/legal/datenschutz.html"


class FaqView(TemplateView):
    template_name = "features/main/legal/faq.html"


class BuchungsregelnView(TemplateView):
    template_name = "features/main/legal/buchungsregeln.html"
