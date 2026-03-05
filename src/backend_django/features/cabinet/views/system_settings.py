"""Unified System Settings View (Site + Booking)."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from features.booking.models.booking_settings import BookingSettings
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.system.models.site_settings import SiteSettings


class SystemSettingsView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    """
    Unified view for managing global site and booking configurations.
    Only for superusers.
    """

    template_name = "cabinet/system/settings/index.html"

    def get_context_data(self, **kwargs):
        # HtmxCabinetMixin and AdminRequiredMixin will contribute to context here
        ctx = super().get_context_data(**kwargs)

        section = self.request.GET.get("section", "site")
        # Ensure section is valid, default to site
        if section not in ["site", "socials", "booking"]:
            section = "site"

        ctx.update(
            {
                "active_section": "system_settings",
                "current_tab": section,
                "site_settings": SiteSettings.load(),
                "booking_settings": BookingSettings.load(),
            }
        )
        return ctx

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        action = request.POST.get("action")

        if action == "save_site":
            self._save_site_settings(request)
        elif action == "save_booking":
            self._save_booking_settings(request)

        if request.headers.get("HX-Request"):
            # For HTMX, we can either refresh or return the updated context
            # Refreshing is safer to ensure all components see new data
            response = HttpResponse()
            response["HX-Refresh"] = "true"
            return response

        return redirect(f"{request.path}?section={request.POST.get('section', 'site')}")

    def _save_site_settings(self, request: HttpRequest):
        s = SiteSettings.load()
        try:
            # Business Details
            s.company_name = request.POST.get("company_name", s.company_name)
            s.owner_name = request.POST.get("owner_name", s.owner_name)

            # Address
            s.address_street = request.POST.get("address_street", s.address_street)
            s.address_locality = request.POST.get("address_locality", s.address_locality)
            s.address_postal_code = request.POST.get("address_postal_code", s.address_postal_code)

            # Contacts & Socials (from socials tab)
            if request.POST.get("section") == "socials":
                s.phone = request.POST.get("phone", s.phone)
                s.email = request.POST.get("email", s.email)
                s.instagram_url = request.POST.get("instagram_url", "")
                s.telegram_url = request.POST.get("telegram_url", "")
                s.whatsapp_url = request.POST.get("whatsapp_url", "")

            s.save()
            messages.success(request, _("Site settings updated."))
        except Exception as e:
            messages.error(request, f"Error: {e}")

    def _save_booking_settings(self, request: HttpRequest):
        b = BookingSettings.load()
        try:
            b.default_step_minutes = int(request.POST.get("default_step_minutes", 30))
            b.default_buffer_between_minutes = int(request.POST.get("default_buffer_between_minutes", 0))
            b.default_min_advance_minutes = int(request.POST.get("default_min_advance_minutes", 60))
            b.default_max_advance_days = int(request.POST.get("default_max_advance_days", 60))
            b.save()
            messages.success(request, _("Booking rules updated."))
        except Exception as e:
            messages.error(request, f"Error: {e}")
