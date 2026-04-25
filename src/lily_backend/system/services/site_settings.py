from __future__ import annotations

from typing import TYPE_CHECKING, Any

from codex_django.cabinet.services.site_settings import SiteSettingsService as LibrarySiteSettingsService
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.http import HttpRequest


class SiteSettingsService(LibrarySiteSettingsService):
    """
    Project-specific Site Settings Service.
    Registers additional tabs for the Lily project.
    """

    TABS_CONFIG = LibrarySiteSettingsService.TABS_CONFIG | {
        "general": {"label": _("General"), "icon": "bi-info-circle"},
        "notifications": {"label": _("Notifications"), "icon": "bi-bell"},
        "work_hours": {"label": _("Work Hours"), "icon": "bi-clock"},
        "hiring": {"label": _("Hiring"), "icon": "bi-person-plus"},
        "technical": {"label": _("Technical Settings"), "icon": "bi-tools"},
    }

    @classmethod
    def save_context(cls, request: HttpRequest) -> tuple[bool, str]:
        return super().save_context(request)

    @classmethod
    def get_context(cls, request: HttpRequest) -> dict[str, Any]:
        from features.notifications.models import NotificationRecipient

        context = super().get_context(request)
        context["recipients"] = NotificationRecipient.objects.all().order_by("-enabled", "email")
        return context
