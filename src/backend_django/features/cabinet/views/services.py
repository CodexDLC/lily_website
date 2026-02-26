"""Services list view (Admin only)."""

import contextlib
from itertools import groupby

from core.logger import log
from django.core.cache import cache
from django.http import JsonResponse
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.main.models.service import Service


class ServicesView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/services/list.html"

    def get_context_data(self, **kwargs):
        log.debug(f"View: ServicesView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "services"
        services = Service.objects.select_related("category").order_by("category__order", "category__title", "order")

        # Group by category
        groups = []
        for category, items in groupby(services, key=lambda s: s.category):
            groups.append((category, list(items)))
        ctx["service_groups"] = groups

        log.info(
            f"View: ServicesView | Action: Success | categories_count={len(groups)} | total_services={services.count()}"
        )
        return ctx

    def post(self, request, *args, **kwargs):
        service_id = request.POST.get("service_id")
        log.info(f"View: ServicesView | Action: UpdateService | service_id={service_id} | user={request.user.id}")

        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            log.error(f"View: ServicesView | Action: UpdateFailed | service_id={service_id} | error=NotFound")
            return JsonResponse({"ok": False, "error": "not found"}, status=404)

        try:
            price_raw = request.POST.get("price", "").strip()
            if price_raw:
                service.price = float(price_raw.replace(",", "."))
                log.debug(f"View: ServicesView | Action: ChangePrice | service_id={service_id} | price={service.price}")

            duration_raw = request.POST.get("duration", "").strip()
            if duration_raw and duration_raw.isdigit():
                service.duration = int(duration_raw)
                log.debug(
                    f"View: ServicesView | Action: ChangeDuration | service_id={service_id} | duration={service.duration}"
                )

            service.is_active = request.POST.get("is_active") == "1"
            service.save(update_fields=["price", "duration", "is_active"])
            log.info(f"View: ServicesView | Action: Success | service_id={service_id} | is_active={service.is_active}")

            # Clear related caches
            with contextlib.suppress(Exception):
                cache_keys = ["active_services_cache", "popular_services_cache", "home_bento_cache_v5"]
                cache.delete_many(cache_keys)
                log.debug(f"View: ServicesView | Action: CacheInvalidated | keys={cache_keys}")

        except (ValueError, TypeError) as e:
            log.error(f"View: ServicesView | Action: UpdateFailed | service_id={service_id} | error={e}")
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

        return JsonResponse({"ok": True, "is_active": service.is_active})
