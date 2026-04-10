from __future__ import annotations

from typing import Any

from django.db.models import Prefetch
from django.http import Http404
from django.views.generic import TemplateView
from features.booking.models import Master
from features.booking.providers.runtime import RuntimeBookingProvider

from ..models import ServiceCategory


class HomeView(TemplateView):
    template_name = "features/main/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
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

        # Pre-calculate selection for templates
        categories = (
            ServiceCategory.objects.filter(is_active=True)
            .prefetch_related(
                Prefetch("services", queryset=provider.get_bookable_services_queryset()),
                "masters",
            )
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
        ctx = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug", "")
        provider = RuntimeBookingProvider()
        try:
            category = (
                ServiceCategory.objects.filter(is_active=True)
                .prefetch_related(
                    Prefetch("services", queryset=provider.get_bookable_services_queryset()),
                    "masters",
                )
                .get(slug=slug)
            )
        except ServiceCategory.DoesNotExist:
            raise Http404 from None
        ctx["category"] = category
        ctx["slug"] = slug
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
