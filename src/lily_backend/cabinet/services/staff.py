from __future__ import annotations

import calendar
import datetime as dt
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from system.selectors.masters import MasterSelector

if TYPE_CHECKING:
    from django.http import HttpRequest
    from features.booking.models.master import Master


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

    @classmethod
    def get_days_off_context(
        cls,
        request: HttpRequest,
        *,
        master_id: int | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> dict[str, object]:
        masters = cls._get_days_off_masters()
        selected_master = cls._resolve_selected_master(masters, master_id)
        month_start = cls._resolve_month_start(year, month)
        month_end = cls._month_end(month_start)
        days_off = cls._get_days_off_dates(selected_master, month_start, month_end)
        appointment_counts = cls._get_active_appointment_counts(selected_master, month_start, month_end)
        prev_month = cls._shift_month(month_start, -1)
        next_month = cls._shift_month(month_start, 1)

        return {
            "header_title": str(_("Days off")),
            "header_subtitle": str(_("Mark master vacation and unavailable days.")),
            "masters": masters,
            "selected_master": selected_master,
            "calendar_weeks": cls._build_month_weeks(month_start, days_off, appointment_counts),
            "month_start": month_start,
            "month_label": month_start.strftime("%B %Y"),
            "prev_month": prev_month,
            "next_month": next_month,
            "selected_days_count": len(days_off),
            "active_appointment_count": sum(appointment_counts.values()),
        }

    @classmethod
    @transaction.atomic
    def save_days_off(
        cls,
        *,
        master_id: int,
        year: int,
        month: int,
        selected_dates: list[str],
    ) -> dict[str, object]:
        from features.booking.models.master import Master
        from features.booking.models.schedule import MasterDayOff

        master = Master.objects.get(pk=master_id)
        month_start = cls._resolve_month_start(year, month)
        month_end = cls._month_end(month_start)
        existing_dates = set(
            MasterDayOff.objects.filter(master=master, date__gte=month_start, date__lte=month_end).values_list(
                "date", flat=True
            )
        )
        requested_dates = cls._parse_dates_for_month(selected_dates, month_start, month_end)
        blocked_dates = set(cls._get_active_appointment_counts(master, month_start, month_end))

        dates_to_create = sorted(requested_dates - existing_dates - blocked_dates)
        dates_to_delete = sorted(existing_dates - requested_dates)

        for day in dates_to_create:
            MasterDayOff.objects.get_or_create(master=master, date=day)

        if dates_to_delete:
            MasterDayOff.objects.filter(master=master, date__in=dates_to_delete).delete()

        return {
            "master": master,
            "created": len(dates_to_create),
            "deleted": len(dates_to_delete),
            "blocked_dates": sorted((requested_dates - existing_dates) & blocked_dates),
        }

    @staticmethod
    def _get_days_off_masters() -> list[Master]:
        from features.booking.models.master import Master

        return list(Master.objects.order_by("order", "name"))

    @staticmethod
    def _resolve_selected_master(masters: list[Master], master_id: int | None) -> Master | None:
        if not masters:
            return None
        if master_id is None:
            return masters[0]
        return next((master for master in masters if master.pk == master_id), masters[0])

    @staticmethod
    def _resolve_month_start(year: int | None, month: int | None) -> dt.date:
        today = dt.date.today()
        try:
            return dt.date(year or today.year, month or today.month, 1)
        except ValueError:
            return dt.date(today.year, today.month, 1)

    @staticmethod
    def _month_end(month_start: dt.date) -> dt.date:
        _, days_in_month = calendar.monthrange(month_start.year, month_start.month)
        return month_start.replace(day=days_in_month)

    @staticmethod
    def _shift_month(month_start: dt.date, delta: int) -> dt.date:
        month_index = month_start.month - 1 + delta
        year = month_start.year + month_index // 12
        month = month_index % 12 + 1
        return dt.date(year, month, 1)

    @staticmethod
    def _get_days_off_dates(master: Master | None, month_start: dt.date, month_end: dt.date) -> set[dt.date]:
        if master is None:
            return set()

        from features.booking.models.schedule import MasterDayOff

        return set(
            MasterDayOff.objects.filter(master=master, date__gte=month_start, date__lte=month_end).values_list(
                "date", flat=True
            )
        )

    @staticmethod
    def _get_active_appointment_counts(
        master: Master | None,
        month_start: dt.date,
        month_end: dt.date,
    ) -> dict[dt.date, int]:
        if master is None:
            return {}

        from django.db.models import Count
        from django.db.models.functions import TruncDate
        from django.utils import timezone
        from features.booking.models.appointment import Appointment

        start = timezone.make_aware(dt.datetime.combine(month_start, dt.time.min))
        end = timezone.make_aware(dt.datetime.combine(month_end + dt.timedelta(days=1), dt.time.min))
        rows = (
            Appointment.objects.filter(
                master=master,
                datetime_start__gte=start,
                datetime_start__lt=end,
                status__in=[
                    Appointment.STATUS_PENDING,
                    Appointment.STATUS_CONFIRMED,
                    Appointment.STATUS_RESCHEDULE_PROPOSED,
                ],
            )
            .annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(count=Count("id"))
        )
        return {row["day"]: row["count"] for row in rows}

    @classmethod
    def _build_month_weeks(
        cls,
        month_start: dt.date,
        days_off: set[dt.date],
        appointment_counts: dict[dt.date, int],
    ) -> list[list[dict[str, object]]]:
        today = dt.date.today()
        weeks = []
        for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month_start.year, month_start.month):
            weeks.append(
                [
                    {
                        "date": day,
                        "iso": day.isoformat(),
                        "day": day.day,
                        "is_current_month": day.month == month_start.month,
                        "is_today": day == today,
                        "is_day_off": day in days_off,
                        "appointment_count": appointment_counts.get(day, 0),
                    }
                    for day in week
                ]
            )
        return weeks

    @staticmethod
    def _parse_dates_for_month(selected_dates: list[str], month_start: dt.date, month_end: dt.date) -> set[dt.date]:
        parsed_dates = set()
        for value in selected_dates:
            try:
                day = dt.date.fromisoformat(value)
            except ValueError:
                continue
            if month_start <= day <= month_end:
                parsed_dates.add(day)
        return parsed_dates
