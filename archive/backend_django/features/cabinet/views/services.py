"""Services list view (Admin only)."""

import contextlib
from itertools import groupby

from core.logger import log
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.main.models.category import Category
from features.main.models.service import Service


class ServicesView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/system/services/list.html"

    def get(self, request, *args, **kwargs):
        action = request.GET.get("action")
        obj_id = request.GET.get("id")

        if action and obj_id:
            if action == "edit_form":
                service = get_object_or_404(Service, id=obj_id)
                return render(request, "cabinet/system/services/includes/_service_edit.html", {"service": service})

            if action == "view_card":
                service = get_object_or_404(Service, id=obj_id)
                return render(request, "cabinet/system/services/includes/_service_card.html", {"service": service})

            if action == "edit_category":
                category = get_object_or_404(Category, id=obj_id)
                return render(request, "cabinet/system/services/includes/_category_edit.html", {"category": category})

            if action == "view_category":
                category = get_object_or_404(Category, id=obj_id)
                return render(request, "cabinet/system/services/includes/_category_header.html", {"category": category})

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        obj_id = request.POST.get("id")

        log.info(f"View: ServicesView | Action: {action} | id={obj_id}")

        try:
            if action == "update":
                service = get_object_or_404(Service, id=obj_id)
                # Update multilingual fields if provided, else fallback to single title
                if "title_de" in request.POST:
                    service.title_de = request.POST.get("title_de")
                    service.title_ru = request.POST.get("title_ru")
                    service.title_en = request.POST.get("title_en")
                else:
                    service.title = request.POST.get("title")

                service.price = request.POST.get("price")
                service.duration = request.POST.get("duration")
                service.is_active = request.POST.get("is_active") == "on"
                service.save()
                self._clear_cache()
                return render(request, "cabinet/system/services/includes/_service_card.html", {"service": service})

            if action == "update_category":
                category = get_object_or_404(Category, id=obj_id)
                category.title_de = request.POST.get("title_de")
                category.title_ru = request.POST.get("title_ru")
                category.title_en = request.POST.get("title_en")
                category.is_active = request.POST.get("is_active") == "on"
                category.save()
                self._clear_cache()
                return render(request, "cabinet/system/services/includes/_category_header.html", {"category": category})

        except Exception as e:
            log.error(f"View: ServicesView | Error: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "services"
        services = Service.objects.select_related("category").order_by("category__order", "category__title", "order")

        groups = []
        for category, items in groupby(services, key=lambda s: s.category):
            groups.append((category, list(items)))
        ctx["service_groups"] = groups

        return ctx

    def _clear_cache(self):
        with contextlib.suppress(Exception):
            cache_keys = ["active_services_cache", "popular_services_cache", "home_bento_cache_v5"]
            cache.delete_many(cache_keys)
