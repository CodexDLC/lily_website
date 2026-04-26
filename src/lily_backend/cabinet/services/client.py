from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from codex_django.cabinet import DataTableData, MetricWidgetData, TableAction, TableColumn
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from features.booking.models import Appointment
from system.selectors.client_profile import ClientProfileSelector
from system.services.loyalty import LoyaltyService

if TYPE_CHECKING:
    from django.http import HttpRequest
    from system.models import Client, UserProfile


@dataclass(frozen=True)
class ClientSummaryCard:
    label: str
    value: str
    hint: str = ""
    icon: str = ""


@dataclass(frozen=True)
class ClientAppointmentRow:
    date_label: str
    time_range: str
    service: str
    specialist: str
    specialist_initials: str
    specialist_color: str
    status: str
    status_tone: str
    total: str = ""
    finalize_token: str = ""


class ClientService:
    STATUS_COLOR_MAP: ClassVar[dict[str, str]] = {
        "confirmed": "success",
        "pending": "warning",
        "completed": "success",
        "cancelled": "danger",
    }

    @staticmethod
    def _format_specialist_cell(row: ClientAppointmentRow) -> str:
        return format_html(
            '<div class="d-flex align-items-center gap-2">'
            '<span class="rounded-circle d-inline-flex align-items-center justify-content-center '
            'text-white small fw-semibold" style="width:30px;height:30px;background:{};">{}</span>'
            "<span>{}</span>"
            "</div>",
            row.specialist_color,
            row.specialist_initials,
            row.specialist,
        )

    @staticmethod
    def _format_datetime_cell(row: ClientAppointmentRow) -> str:
        if not row.time_range:
            return row.date_label
        return format_html(
            '<div class="fw-semibold">{}</div><div class="text-muted small">{}</div>',
            row.date_label,
            row.time_range,
        )

    @classmethod
    def _build_upcoming_table(cls, rows: list[ClientAppointmentRow]) -> DataTableData:
        return DataTableData(
            columns=[
                TableColumn(key="datetime", label=str(_("Date and Time")), bold=True),
                TableColumn(key="service", label=str(_("Service"))),
                TableColumn(key="specialist", label=str(_("Specialist"))),
                TableColumn(
                    key="status_label",
                    label=str(_("Status")),
                    badge_key="status_color_map",
                ),
            ],
            rows=[
                {
                    "datetime": cls._format_datetime_cell(row),
                    "service": row.service,
                    "specialist": cls._format_specialist_cell(row),
                    "status": row.status_tone,
                    "status_label": row.status,
                    "status_color_map": cls.STATUS_COLOR_MAP,
                    "manage_url": f"/cabinet/my/appointments/manage/{row.finalize_token}/"
                    if row.finalize_token
                    else "#",
                }
                for row in rows
            ],
            actions=[
                TableAction(
                    label=str(_("Manage")),
                    url_key="manage_url",
                    style="btn-outline-primary",
                )
            ],
            empty_message=str(_("No upcoming appointments yet.")),
        )

    @classmethod
    def _build_history_table(cls, rows: list[ClientAppointmentRow]) -> DataTableData:
        return DataTableData(
            columns=[
                TableColumn(key="date", label=str(_("Date")), bold=True),
                TableColumn(key="service", label=str(_("Service"))),
                TableColumn(key="specialist", label=str(_("Specialist"))),
                TableColumn(key="total", label=str(_("Total")), align="right"),
                TableColumn(
                    key="status_label",
                    label=str(_("Status")),
                    badge_key="status_color_map",
                ),
            ],
            rows=[
                {
                    "date": row.date_label,
                    "service": row.service,
                    "specialist": row.specialist,
                    "total": row.total,
                    "status": row.status_tone,
                    "status_label": row.status,
                    "status_color_map": cls.STATUS_COLOR_MAP,
                }
                for row in rows
            ],
            empty_message=str(_("No appointment history yet.")),
        )

    @classmethod
    def get_corner_context(cls, request: HttpRequest) -> dict[str, object]:
        user = request.user
        profile: UserProfile | None = getattr(user, "profile", None)
        client: Client | None = getattr(user, "client_profile", None)
        if profile is None and getattr(user, "is_authenticated", False):
            profile = ClientProfileSelector.get_or_create_profile(user)

        if client:
            first_name = client.first_name or user.username
            last_name = client.last_name
            initials = "".join(p[0].upper() for p in [client.first_name, client.last_name] if p) or "?"
            profile_form = {
                "first_name": client.first_name,
                "last_name": client.last_name,
                "patronymic": client.patronymic,
                "phone": client.phone or "",
                "email": client.email or "",
                "birth_date": profile.birth_date.isoformat() if profile and profile.birth_date else "",
                "instagram": profile.instagram if profile else "",
                "telegram": profile.telegram if profile else "",
                "notify_service": profile.notify_service if profile else True,
                "notify_reminders": profile.notify_reminders if profile else True,
            }
            joined_at = client.created_at.date()
        elif profile:
            first_name = profile.first_name or user.username
            last_name = profile.last_name
            initials = profile.get_initials()
            profile_form = {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "patronymic": "",
                "phone": "",
                "email": user.email or "",
                "birth_date": profile.birth_date.isoformat() if profile.birth_date else "",
                "instagram": profile.instagram,
                "telegram": profile.telegram,
                "notify_service": profile.notify_service,
                "notify_reminders": profile.notify_reminders,
            }
            joined_at = profile.created_at.date()
        else:
            first_name = user.username
            last_name = ""
            initials = "?"
            profile_form = {}
            joined_at = getattr(user, "date_joined", timezone.now()).date()

        if client:
            qs = Appointment.objects.filter(client=client)
            total_visits = qs.filter(status="completed").count()
            total_spent = qs.filter(status="completed").aggregate(t=Sum("price"))["t"] or 0
        else:
            total_visits = 0
            total_spent = 0

        loyalty = LoyaltyService.get_display_for_profile(profile)

        upcoming_preview: list[dict[str, str]] = []
        if client:
            upcoming_qs = (
                Appointment.objects.filter(
                    client=client,
                    status__in=["pending", "confirmed"],
                    datetime_start__gte=timezone.now(),
                )
                .select_related("service", "master")
                .order_by("datetime_start")[:3]
            )
            upcoming_preview = [
                {
                    "date": timezone.localtime(obj.datetime_start).strftime("%d %b"),
                    "time": timezone.localtime(obj.datetime_start).strftime("%H:%M"),
                    "service": obj.service.title,
                    "master": obj.master.name,
                    "status_tone": obj.status,
                    "token": obj.finalize_token or "",
                }
                for obj in upcoming_qs
            ]

        return {
            "client_page_title": _("My Corner"),
            "profile_form": profile_form,
            "loyalty": loyalty,
            "upcoming_preview": upcoming_preview,
            "corner_summary": {
                "display_name": f"{first_name} {last_name}".strip(),
                "subtitle": _("Client since %(month)s %(year)s")
                % {"month": joined_at.strftime("%B"), "year": joined_at.year},
                "initials": initials,
                "stats": [
                    ClientSummaryCard(label=str(_("Visits")), value=str(total_visits)),
                    ClientSummaryCard(label=str(_("Spent")), value=f"€{total_spent:.0f}"),
                ],
            },
        }

    @classmethod
    def save_corner_profile(cls, request: HttpRequest) -> tuple[bool, str]:
        user = request.user
        client = getattr(user, "client_profile", None)
        profile = getattr(user, "profile", None)
        data = request.POST

        if client:
            client.first_name = data.get("first_name", "").strip()
            client.last_name = data.get("last_name", "").strip()
            client.phone = data.get("phone", "").strip()
            client.email = data.get("email", "").strip()
            client.save(update_fields=["first_name", "last_name", "phone", "email", "updated_at"])

        if profile:
            profile.instagram = data.get("instagram", "").strip()
            profile.telegram = data.get("telegram", "").strip()
            profile.notify_service = data.get("notify_service") == "on"
            profile.notify_reminders = data.get("notify_reminders") == "on"
            profile.save(update_fields=["instagram", "telegram", "notify_service", "notify_reminders", "updated_at"])

        return True, str(_("Profile updated successfully."))

    @classmethod
    def get_appointments_context(cls, request: HttpRequest) -> dict[str, object]:
        user = request.user
        client = getattr(user, "client_profile", None)

        if not client:
            return {
                "client_page_title": _("My Appointments"),
                "appointments_stats": [],
                "upcoming_table": cls._build_upcoming_table([]),
                "history_table": cls._build_history_table([]),
                "history_total_count": 0,
                "history_visible_count": 0,
            }

        all_appointments = Appointment.objects.filter(client=client).select_related("service", "master")

        upcoming_objs = all_appointments.filter(status__in=["pending", "confirmed"], datetime_start__gte=timezone.now())
        history_objs = all_appointments.exclude(id__in=upcoming_objs.values_list("id", flat=True))

        upcoming_rows = [
            ClientAppointmentRow(
                date_label=timezone.localtime(obj.datetime_start).strftime("%d %B %Y"),
                time_range=f"{timezone.localtime(obj.datetime_start).strftime('%H:%M')} — {timezone.localtime(obj.datetime_start + timezone.timedelta(minutes=obj.duration_minutes)).strftime('%H:%M')}",
                service=obj.service.title,
                specialist=obj.master.name,
                specialist_initials=obj.master.name[0].upper() if obj.master.name else "?",
                specialist_color="#7c3aed",
                status=obj.get_status_display(),
                status_tone=obj.status,
                finalize_token=obj.finalize_token,
            )
            for obj in upcoming_objs
        ]

        history_rows = [
            ClientAppointmentRow(
                date_label=timezone.localtime(obj.datetime_start).strftime("%d %B %Y"),
                time_range="",
                service=obj.service.title,
                specialist=obj.master.name,
                specialist_initials="",
                specialist_color="",
                status=obj.get_status_display(),
                status_tone=obj.status,
                total=f"€{obj.price:.0f}",
            )
            for obj in history_objs[:10]
        ]

        return {
            "client_page_title": _("My Appointments"),
            "appointments_stats": [
                MetricWidgetData(
                    label=str(_("Upcoming")),
                    value=str(upcoming_objs.count()),
                    trend_label=str(_("scheduled")),
                    icon="bi-calendar2-check",
                ),
                MetricWidgetData(
                    label=str(_("Completed")),
                    value=str(history_objs.filter(status="completed").count()),
                    trend_label=str(_("visits total")),
                    icon="bi-check-circle",
                ),
                MetricWidgetData(
                    label=str(_("Pending")),
                    value=str(upcoming_objs.filter(status="pending").count()),
                    trend_label=str(_("awaiting confirmation")),
                    icon="bi-clock-history",
                ),
            ],
            "upcoming_table": cls._build_upcoming_table(upcoming_rows),
            "history_table": cls._build_history_table(history_rows),
            "history_total_count": history_objs.count(),
            "history_visible_count": len(history_rows),
        }
