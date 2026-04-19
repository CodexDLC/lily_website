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
        "work_hours": {"label": _("Work Hours"), "icon": "bi-clock"},
        "hiring": {"label": _("Hiring"), "icon": "bi-person-plus"},
        "technical": {"label": _("Technical Settings"), "icon": "bi-tools"},
    }

    @staticmethod
    def save_context(request: HttpRequest) -> tuple[bool, str]:
        return LibrarySiteSettingsService.save_context(request)  # type: ignore[no-any-return]

    @staticmethod
    def get_context(request: HttpRequest) -> dict[str, Any]:
        return LibrarySiteSettingsService.get_context(request)  # type: ignore[no-any-return]
