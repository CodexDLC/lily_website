"""Services list view (Admin only)."""

import contextlib
from itertools import groupby

from django.core.cache import cache
from django.http import JsonResponse
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.main.models.service import Service


class ServicesView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/services/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "services"
        services = Service.objects.select_related("category").order_by("category__order", "category__title", "order")
        # Group by category
        groups = []
        for category, items in groupby(services, key=lambda s: s.category):
            groups.append((category, list(items)))
        ctx["service_groups"] = groups
        return ctx

    def post(self, request, *args, **kwargs):
        service_id = request.POST.get("service_id")
        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            return JsonResponse({"ok": False, "error": "not found"}, status=404)

        try:
            price_raw = request.POST.get("price", "").strip()
            if price_raw:
                service.price = float(price_raw.replace(",", "."))

            duration_raw = request.POST.get("duration", "").strip()
            if duration_raw and duration_raw.isdigit():
                service.duration = int(duration_raw)

            service.is_active = request.POST.get("is_active") == "1"
            service.save(update_fields=["price", "duration", "is_active"])

            # Clear related caches
            with contextlib.suppress(Exception):
                cache.delete_many(["active_services_cache", "popular_services_cache", "home_bento_cache_v5"])

        except (ValueError, TypeError) as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

        return JsonResponse({"ok": True, "is_active": service.is_active})
