from __future__ import annotations

from typing import TYPE_CHECKING

from codex_django.cabinet.types import CardGridData, CardItem
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models import QuerySet


class MasterSelector:
    WEEKDAY_LABELS = {
        0: "Mo",
        1: "Tu",
        2: "We",
        3: "Th",
        4: "Fr",
        5: "Sa",
        6: "Su",
    }

    @staticmethod
    def get_masters_queryset() -> QuerySet:
        from features.booking.models.master import Master

        return Master.objects.prefetch_related("categories", "working_days", "services").all().order_by("order", "name")

    @classmethod
    def get_masters_grid(cls) -> CardGridData:
        queryset = cls.get_masters_queryset()
        items = []

        for master in queryset:
            working_days = sorted(master.working_days.values_list("weekday", flat=True))
            assigned_services_count = master.services.filter(is_active=True).count()
            has_schedule = bool(working_days)
            is_bookable_ready = master.status == "active" and has_schedule and assigned_services_count > 0

            # Determine badge style based on status/readiness
            badge_style = "success"
            if master.status == "vacation":
                badge_style = "warning"
            elif master.status == "training":
                badge_style = "info"
            elif master.status == "inactive":
                badge_style = "secondary"
            elif not is_bookable_ready:
                badge_style = "warning"

            avatar = master.photo.url if master.photo else (master.name[0].upper() if master.name else "?")

            # Specialties from categories
            specialties = ", ".join([cat.name for cat in master.categories.all()[:2]])
            subtitle = f"{master.title or str(_('Specialist'))}"
            if specialties:
                subtitle = f"{subtitle} • {specialties}"

            meta = []
            if master.phone:
                meta.append(("bi-telephone", master.phone))

            if master.years_experience:
                meta.append(("bi-star", f"{master.years_experience} {str(_('years'))}"))

            if master.is_owner:
                meta.append(("bi-patch-check", str(_("Owner"))))

            if working_days:
                weekday_line = " ".join(cls.WEEKDAY_LABELS.get(day, str(day)) for day in working_days)
                meta.append(("bi-calendar3", weekday_line))
            else:
                meta.append(("bi-calendar-x", str(_("No working days"))))

            meta.append(("bi-scissors", f"{assigned_services_count} {str(_('services assigned'))}"))

            meta.append(
                (
                    "bi-eye" if master.is_public else "bi-eye-slash",
                    str(_("Public")) if master.is_public else str(_("Hidden")),
                )
            )

            if not is_bookable_ready:
                if assigned_services_count == 0:
                    meta.append(("bi-exclamation-triangle", str(_("No services linked for booking"))))
                elif not has_schedule:
                    meta.append(("bi-exclamation-triangle", str(_("No working schedule for booking"))))

            items.append(
                CardItem(
                    id=f"master_{master.pk}",
                    title=master.name,
                    subtitle=subtitle,
                    avatar=avatar,
                    badge=str(_("Booking Ready")) if is_bookable_ready else master.get_status_display(),
                    badge_style=badge_style,
                    url=str(reverse_lazy("cabinet:staff_modal", kwargs={"pk": master.pk})),
                    meta=meta,
                )
            )

        return CardGridData(
            items=items,
            search_placeholder=str(_("Search staff...")),
            empty_message=str(_("No staff members found")),
            view_mode="grid",
        )
