"""
Booking Settings View for Cabinet.

Allows editing the BookingSettings singleton.
"""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import View
from features.booking.models import BookingSettings


class BookingSettingsView(UserPassesTestMixin, View):
    """
    View for editing BookingSettings.
    Only for superusers (admin).
    """

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request: HttpRequest) -> HttpResponse:
        settings = BookingSettings.load()
        context = {
            "active_section": "booking_settings",
            "settings": settings,
        }

        if request.headers.get("HX-Request"):
            return render(request, "cabinet/system/pages/booking_settings_htmx.html", context)
        return render(request, "cabinet/system/pages/booking_settings.html", context)

    def post(self, request: HttpRequest) -> HttpResponse:
        settings = BookingSettings.load()

        try:
            settings.default_step_minutes = int(request.POST.get("default_step_minutes", 30))
            settings.default_work_start = request.POST.get("default_work_start", "09:00")
            settings.default_work_end = request.POST.get("default_work_end", "18:00")
            settings.default_buffer_between_minutes = int(request.POST.get("default_buffer_between_minutes", 0))
            settings.default_min_advance_minutes = int(request.POST.get("default_min_advance_minutes", 60))
            settings.default_max_advance_days = int(request.POST.get("default_max_advance_days", 60))

            settings.save()
            messages.success(request, _("Настройки записи успешно сохранены."))
        except (ValueError, TypeError):
            messages.error(request, _("Ошибка при сохранении: неверный формат данных."))

        # HTMX Redirect headers support
        if request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = request.path
            return response
        return redirect("cabinet:booking_settings")
