import contextlib
from datetime import datetime
from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from cabinet.services.client import ClientService

if TYPE_CHECKING:
    from system.models import Client, UserProfile


class ClientHomeView(TemplateView):
    template_name = "cabinet/client/corner.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_space = "client"
        request.cabinet_module = "client"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(ClientService.get_corner_context(self.request))
        return context


class ClientAppointmentsView(TemplateView):
    template_name = "cabinet/client/appointments.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_space = "client"
        request.cabinet_module = "client"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(ClientService.get_appointments_context(self.request))
        return context


class ClientSettingsView(TemplateView):
    template_name = "cabinet/client/settings.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_space = "client"
        request.cabinet_module = "client_settings"
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        action = request.POST.get("action")
        user = request.user
        client: Client | None = getattr(user, "client_profile", None)
        profile: UserProfile | None = getattr(user, "profile", None)

        if action == "profile":
            if client:
                client.first_name = request.POST.get("first_name", "").strip()
                client.last_name = request.POST.get("last_name", "").strip()
                client.patronymic = request.POST.get("patronymic", "").strip()
                client.phone = request.POST.get("phone", "").strip()
                client.email = request.POST.get("email", "").strip()
                client.save(update_fields=["first_name", "last_name", "patronymic", "phone", "email", "updated_at"])

            if profile:
                profile.instagram = request.POST.get("instagram", "").strip()
                profile.telegram = request.POST.get("telegram", "").strip()
                birth_date_raw = request.POST.get("birth_date", "").strip()
                if birth_date_raw:
                    with contextlib.suppress(Exception):
                        profile.birth_date = datetime.strptime(birth_date_raw, "%Y-%m-%d").date()
                else:
                    profile.birth_date = None
                profile.save(update_fields=["instagram", "telegram", "birth_date", "updated_at"])

            messages.success(request, _("Profile updated successfully."))

        elif action == "notifications":
            if client:
                client.consent_marketing = request.POST.get("consent_marketing") == "on"
                client.consent_date = timezone.now()
                client.save(update_fields=["consent_marketing", "consent_date", "updated_at"])

            if profile:
                profile.notify_service = request.POST.get("notify_service") == "on"
                profile.notify_reminders = request.POST.get("notify_reminders") == "on"
                profile.save(update_fields=["notify_service", "notify_reminders", "updated_at"])

            messages.success(request, _("Notification preferences saved."))

        elif action == "privacy":
            if profile:
                profile.show_avatar = request.POST.get("show_avatar") == "on"
                profile.show_birth_date = request.POST.get("show_birth_date") == "on"
                profile.show_visit_history = request.POST.get("show_visit_history") == "on"
                profile.use_recommendations = request.POST.get("use_recommendations") == "on"
                profile.save(
                    update_fields=[
                        "show_avatar",
                        "show_birth_date",
                        "show_visit_history",
                        "use_recommendations",
                        "updated_at",
                    ]
                )

            if client:
                client.consent_analytics = request.POST.get("consent_analytics") == "on"
                client.save(update_fields=["consent_analytics", "updated_at"])

            messages.success(request, _("Privacy settings saved."))

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user

        client = getattr(user, "client_profile", None)
        profile = getattr(user, "profile", None)

        context.update(
            {
                "client": client,
                "profile": profile,
                "active_tab": self.request.GET.get("tab", "account"),
            }
        )
        return context
