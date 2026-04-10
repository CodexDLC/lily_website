from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from system.selectors.masters import MasterSelector

if TYPE_CHECKING:
    from django.http import HttpRequest


class StaffService:
    """Service for cabinet staff management."""

    @classmethod
    def get_list_context(cls, request: HttpRequest) -> dict[str, object]:
        return {
            "cards": MasterSelector.get_masters_grid(),
            "header_title": str(_("Personnel")),
            "header_subtitle": str(_("Our Team")),
        }

    @classmethod
    def get_master_detail(cls, pk: int) -> dict[str, object]:
        from features.booking.models.master import Master

        master = Master.objects.filter(pk=pk).first()
        return {"master": master}
