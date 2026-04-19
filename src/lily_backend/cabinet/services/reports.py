from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

from codex_django.cabinet import (
    ChartAxisData,
    ChartDatasetData,
    ReportChartData,
    ReportPageData,
    ReportSummaryCardData,
    ReportTabData,
    ReportTableData,
    TableColumn,
    resolve_report_period,
)
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.http import HttpRequest


MONEY_AXIS_COLOR = "#2563eb"
BOOKING_AXIS_COLOR = "#14b8a6"
SERVICE_AXIS_COLOR = "#7c3aed"
CLIENT_AXIS_COLOR = "#f97316"


def _date_keys(period_from: date, period_to: date) -> list[date]:
    days = (period_to - period_from).days + 1
    return [period_from + timedelta(days=offset) for offset in range(max(days, 0))]


def _day_label(day: date) -> str:
    return day.strftime("%d.%m")


def _money(value: Decimal | int | float | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _format_money(value: Decimal | int | float | None) -> str:
    amount = _money(value)
    return f"€{amount:,.0f}".replace(",", " ")


def _format_percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.0f}%"


def _growth(current: Decimal | int | float, previous: Decimal | int | float) -> tuple[str | None, str]:
    previous_value = _money(previous)
    if not previous_value:
        return None, "neutral"
    current_value = _money(current)
    diff = ((current_value - previous_value) / previous_value) * Decimal("100")
    direction = "up" if diff >= 0 else "down"
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:.0f}%", direction


def _price_expr() -> Coalesce:
    return Coalesce("price_actual", "price", output_field=DecimalField(max_digits=10, decimal_places=2))


def _appointment_statuses() -> tuple[list[str], list[str]]:
    from features.booking.models import Appointment

    revenue_statuses = [Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED]
    counted_statuses = [
        Appointment.STATUS_PENDING,
        Appointment.STATUS_CONFIRMED,
        Appointment.STATUS_COMPLETED,
        Appointment.STATUS_RESCHEDULE_PROPOSED,
    ]
    return revenue_statuses, counted_statuses


@dataclass
class LilyReportsService:
    @staticmethod
    def build(request: HttpRequest) -> ReportPageData:
        period = resolve_report_period(
            request.GET.get("period"),
            date_from=request.GET.get("date_from"),
            date_to=request.GET.get("date_to"),
        )
        active_tab = request.GET.get("tab", "revenue")
        if active_tab not in {"revenue", "services", "clients"}:
            active_tab = "revenue"

        tabs: list[ReportTabData | dict[str, Any]] = [
            ReportTabData(key="revenue", label=str(_("Revenue")), icon="bi-currency-euro"),
            ReportTabData(key="services", label=str(_("Services")), icon="bi-scissors"),
            ReportTabData(key="clients", label=str(_("Clients")), icon="bi-people"),
        ]
        period_options: list[ReportTabData | dict[str, Any]] = [
            ReportTabData(key="week", label=str(_("Week"))),
            ReportTabData(key="month", label=str(_("Month"))),
            ReportTabData(key="quarter", label=str(_("Quarter"))),
            ReportTabData(key="year", label=str(_("Year"))),
        ]
        builders = {
            "revenue": LilyReportsService._revenue_report,
            "services": LilyReportsService._services_report,
            "clients": LilyReportsService._clients_report,
        }
        payload = builders[active_tab](period)
        return ReportPageData(
            title=str(_("Reports")),
            summary=payload["summary"],
            active_tab=active_tab,
            active_period=period.key,
            tabs=tabs,
            period_options=period_options,
            period_label=f"{period.date_from:%d.%m.%Y} - {period.date_to:%d.%m.%Y}",
            summary_cards=payload["summary_cards"],
            table=payload["table"],
            chart=payload["chart"],
        )

    @staticmethod
    def _base_appointments(period_from: date, period_to: date, statuses: Iterable[str] | None = None) -> Any:
        from features.booking.models import Appointment

        qs = Appointment.objects.filter(datetime_start__date__gte=period_from, datetime_start__date__lte=period_to)
        if statuses is not None:
            qs = qs.filter(status__in=list(statuses))
        return qs

    @staticmethod
    def _revenue_report(period: Any) -> dict[str, Any]:
        from features.booking.models import Appointment

        revenue_statuses, counted_statuses = _appointment_statuses()
        revenue_qs = LilyReportsService._base_appointments(period.date_from, period.date_to, revenue_statuses)
        bookings_qs = LilyReportsService._base_appointments(period.date_from, period.date_to, counted_statuses)
        previous_revenue_qs = LilyReportsService._base_appointments(
            period.previous_from, period.previous_to, revenue_statuses
        )
        previous_bookings_qs = LilyReportsService._base_appointments(
            period.previous_from, period.previous_to, counted_statuses
        )

        revenue_total = _money(revenue_qs.aggregate(total=Sum(_price_expr()))["total"])
        previous_revenue = _money(previous_revenue_qs.aggregate(total=Sum(_price_expr()))["total"])
        booking_count = bookings_qs.count()
        completed_count = bookings_qs.filter(status=Appointment.STATUS_COMPLETED).count()
        average_check = revenue_total / booking_count if booking_count else Decimal("0")
        completion_rate = (completed_count / booking_count) * 100 if booking_count else None
        trend_value, trend_direction = _growth(revenue_total, previous_revenue)

        daily_revenue = {
            row["day"]: _money(row["revenue"])
            for row in revenue_qs.annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(revenue=Sum(_price_expr()))
        }
        daily_bookings = {
            row["day"]: row["bookings"]
            for row in bookings_qs.annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(bookings=Count("id"))
        }
        daily_completed = {
            row["day"]: row["completed"]
            for row in bookings_qs.annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(completed=Count("id", filter=Q(status=Appointment.STATUS_COMPLETED)))
        }

        labels: list[str] = []
        revenue_values: list[float] = []
        booking_values: list[int] = []
        rows: list[dict[str, Any]] = []
        for day in _date_keys(period.date_from, period.date_to):
            day_revenue = daily_revenue.get(day, Decimal("0"))
            day_bookings = daily_bookings.get(day, 0)
            day_completed = daily_completed.get(day, 0)
            labels.append(_day_label(day))
            revenue_values.append(float(day_revenue))
            booking_values.append(day_bookings)
            rows.append(
                {
                    "day": _day_label(day),
                    "revenue": _format_money(day_revenue),
                    "bookings": day_bookings,
                    "avg_check": _format_money(day_revenue / day_bookings if day_bookings else Decimal("0")),
                    "completed": f"{day_completed} / {day_bookings}",
                }
            )

        return {
            "summary": str(_("Revenue and appointment volume for the selected period.")),
            "summary_cards": [
                ReportSummaryCardData(
                    label=str(_("Revenue")),
                    value=_format_money(revenue_total),
                    hint=str(_("vs previous period")),
                    trend_value=trend_value,
                    trend_direction=trend_direction,
                    icon="bi-currency-euro",
                ),
                ReportSummaryCardData(label=str(_("Bookings")), value=str(booking_count), icon="bi-calendar-check"),
                ReportSummaryCardData(
                    label=str(_("Average check")), value=_format_money(average_check), icon="bi-receipt"
                ),
                ReportSummaryCardData(
                    label=str(_("Completion rate")),
                    value=_format_percent(completion_rate),
                    icon="bi-check2-circle",
                ),
            ],
            "table": ReportTableData(
                title=str(_("Daily detail")),
                subtitle=str(_("Revenue, bookings, average check and completed appointments.")),
                columns=[
                    TableColumn(key="day", label=str(_("Day")), bold=True),
                    TableColumn(key="revenue", label=str(_("Revenue")), align="right"),
                    TableColumn(key="bookings", label=str(_("Bookings")), align="right"),
                    TableColumn(key="avg_check", label=str(_("Average check")), align="right"),
                    TableColumn(key="completed", label=str(_("Completed")), align="right"),
                ],
                rows=rows,
                summary_row={
                    "day": str(_("Total")),
                    "revenue": _format_money(revenue_total),
                    "bookings": booking_count,
                    "avg_check": _format_money(average_check),
                    "completed": f"{completed_count} / {booking_count}",
                },
                primary_summary=_format_money(revenue_total),
                secondary_summary=str(_("Total revenue")),
            ),
            "chart": ReportChartData(
                chart_id="lilyRevenueVolumeChart",
                title=str(_("Revenue and bookings")),
                description=str(_("Bookings use the left axis; revenue uses the right axis.")),
                labels=labels,
                type="bar",
                icon="bi-bar-chart-line",
                datasets=[
                    ChartDatasetData(
                        label=str(_("Bookings")),
                        data=cast("list[int | float | None]", booking_values),
                        type="bar",
                        y_axis_id="y",
                        background_color="rgba(20, 184, 166, 0.32)",
                        border_color=BOOKING_AXIS_COLOR,
                        border_radius=4,
                    ),
                    ChartDatasetData(
                        label=str(_("Revenue")),
                        data=cast("list[int | float | None]", revenue_values),
                        type="line",
                        y_axis_id="y1",
                        border_color=MONEY_AXIS_COLOR,
                        background_color="rgba(37, 99, 235, 0.12)",
                        border_width=2,
                        point_radius=2,
                        tension=0.25,
                        fill=False,
                    ),
                ],
                axes=[
                    ChartAxisData(id="y", position="left", label=str(_("Bookings"))),
                    ChartAxisData(
                        id="y1",
                        position="right",
                        label=str(_("Revenue")),
                        draw_on_chart_area=False,
                        tick_prefix="€",
                    ),
                ],
            ),
            "previous_bookings": previous_bookings_qs.count(),
        }

    @staticmethod
    def _services_report(period: Any) -> dict[str, Any]:
        revenue_statuses, _counted_statuses = _appointment_statuses()
        qs = LilyReportsService._base_appointments(period.date_from, period.date_to, revenue_statuses)
        total_revenue = _money(qs.aggregate(total=Sum(_price_expr()))["total"])
        services = list(
            qs.values("service__name", "service__category__name")
            .annotate(revenue=Sum(_price_expr()), bookings=Count("id"))
            .order_by("-revenue", "-bookings")[:12]
        )
        labels = [row["service__name"] or str(_("Service")) for row in services[:8]]
        revenue_values = [float(_money(row["revenue"])) for row in services[:8]]
        booking_values = [int(row["bookings"] or 0) for row in services[:8]]
        rows = []
        for row in services:
            revenue = _money(row["revenue"])
            bookings = int(row["bookings"] or 0)
            share = (float(revenue / total_revenue) * 100) if total_revenue else 0
            rows.append(
                {
                    "service": row["service__name"] or "—",
                    "category": row["service__category__name"] or "—",
                    "bookings": bookings,
                    "revenue": _format_money(revenue),
                    "avg_check": _format_money(revenue / bookings if bookings else Decimal("0")),
                    "share": f"{share:.0f}%",
                }
            )

        service_count = len(services)
        booking_count = sum(int(row["bookings"] or 0) for row in services)
        avg_service_check = total_revenue / booking_count if booking_count else Decimal("0")
        return {
            "summary": str(_("Service mix by revenue and appointment count.")),
            "summary_cards": [
                ReportSummaryCardData(label=str(_("Services sold")), value=str(service_count), icon="bi-scissors"),
                ReportSummaryCardData(label=str(_("Appointments")), value=str(booking_count), icon="bi-calendar-check"),
                ReportSummaryCardData(
                    label=str(_("Revenue")), value=_format_money(total_revenue), icon="bi-currency-euro"
                ),
                ReportSummaryCardData(
                    label=str(_("Average service check")),
                    value=_format_money(avg_service_check),
                    icon="bi-receipt",
                ),
            ],
            "table": ReportTableData(
                title=str(_("Top services")),
                subtitle=str(_("Ranked by revenue in the selected period.")),
                columns=[
                    TableColumn(key="service", label=str(_("Service")), bold=True),
                    TableColumn(key="category", label=str(_("Category"))),
                    TableColumn(key="bookings", label=str(_("Bookings")), align="right"),
                    TableColumn(key="revenue", label=str(_("Revenue")), align="right"),
                    TableColumn(key="avg_check", label=str(_("Average check")), align="right"),
                    TableColumn(key="share", label=str(_("Share")), align="right"),
                ],
                rows=rows,
                summary_row={
                    "service": str(_("Total")),
                    "category": "",
                    "bookings": booking_count,
                    "revenue": _format_money(total_revenue),
                    "avg_check": _format_money(avg_service_check),
                    "share": "100%" if total_revenue else "—",
                },
                primary_summary=_format_money(total_revenue),
                secondary_summary=str(_("Services revenue")),
            ),
            "chart": ReportChartData(
                chart_id="lilyServicesRevenueChart",
                title=str(_("Top services")),
                labels=labels,
                type="bar",
                icon="bi-scissors",
                datasets=[
                    ChartDatasetData(
                        label=str(_("Revenue")),
                        data=cast("list[int | float | None]", revenue_values),
                        type="bar",
                        y_axis_id="y",
                        background_color="rgba(124, 58, 237, 0.30)",
                        border_color=SERVICE_AXIS_COLOR,
                        border_radius=4,
                    ),
                    ChartDatasetData(
                        label=str(_("Bookings")),
                        data=cast("list[int | float | None]", booking_values),
                        type="line",
                        y_axis_id="y1",
                        border_color=BOOKING_AXIS_COLOR,
                        background_color="rgba(20, 184, 166, 0.14)",
                        border_width=2,
                        point_radius=2,
                        tension=0.25,
                    ),
                ],
                axes=[
                    ChartAxisData(id="y", position="left", label=str(_("Revenue")), tick_prefix="€"),
                    ChartAxisData(
                        id="y1",
                        position="right",
                        label=str(_("Bookings")),
                        draw_on_chart_area=False,
                    ),
                ],
            ),
        }

    @staticmethod
    def _clients_report(period: Any) -> dict[str, Any]:
        from features.conversations.models import Message
        from system.models import Client

        _revenue_statuses, counted_statuses = _appointment_statuses()
        appointments_qs = LilyReportsService._base_appointments(period.date_from, period.date_to, counted_statuses)
        previous_client_ids = set(
            LilyReportsService._base_appointments(date(2000, 1, 1), period.previous_to, counted_statuses)
            .exclude(client_id__isnull=True)
            .values_list("client_id", flat=True)
        )

        new_clients_by_day = {
            row["day"]: row["new_clients"]
            for row in Client.objects.filter(
                created_at__date__gte=period.date_from,
                created_at__date__lte=period.date_to,
            )
            .exclude(status=Client.STATUS_BLOCKED)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(new_clients=Count("id"))
        }
        appointments_by_day = {
            row["day"]: row["appointments"]
            for row in appointments_qs.annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(appointments=Count("id"))
        }
        active_clients_by_day = {
            row["day"]: row["active_clients"]
            for row in appointments_qs.exclude(client_id__isnull=True)
            .annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(active_clients=Count("client_id", distinct=True))
        }
        repeat_clients_by_day = {
            row["day"]: row["repeat_clients"]
            for row in appointments_qs.filter(client_id__in=previous_client_ids)
            .annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(repeat_clients=Count("client_id", distinct=True))
        }
        messages_by_day = {
            row["day"]: row["messages"]
            for row in Message.objects.filter(
                created_at__date__gte=period.date_from,
                created_at__date__lte=period.date_to,
            )
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(messages=Count("id"))
        }

        labels: list[str] = []
        new_client_values: list[int] = []
        appointment_values: list[int] = []
        repeat_client_values: list[int] = []
        rows: list[dict[str, Any]] = []
        for day in _date_keys(period.date_from, period.date_to):
            new_clients = new_clients_by_day.get(day, 0)
            appointments = appointments_by_day.get(day, 0)
            active_clients = active_clients_by_day.get(day, 0)
            repeat_clients = repeat_clients_by_day.get(day, 0)
            messages = messages_by_day.get(day, 0)
            labels.append(_day_label(day))
            new_client_values.append(new_clients)
            appointment_values.append(appointments)
            repeat_client_values.append(repeat_clients)
            rows.append(
                {
                    "day": _day_label(day),
                    "new_clients": new_clients,
                    "active_clients": f"{active_clients} / {appointments}",
                    "repeat_clients": repeat_clients,
                    "messages": messages,
                }
            )

        new_clients_total = sum(new_client_values)
        appointments_total = sum(appointment_values)
        repeat_clients_total = sum(repeat_client_values)
        active_clients_total = appointments_qs.exclude(client_id__isnull=True).values("client_id").distinct().count()
        repeat_rate = (repeat_clients_total / active_clients_total) * 100 if active_clients_total else None

        return {
            "summary": str(_("Client acquisition and repeat activity for the selected period.")),
            "summary_cards": [
                ReportSummaryCardData(label=str(_("New clients")), value=str(new_clients_total), icon="bi-person-plus"),
                ReportSummaryCardData(
                    label=str(_("Active clients")), value=str(active_clients_total), icon="bi-people"
                ),
                ReportSummaryCardData(
                    label=str(_("Repeat clients")), value=str(repeat_clients_total), icon="bi-arrow-repeat"
                ),
                ReportSummaryCardData(
                    label=str(_("Repeat rate")),
                    value=_format_percent(repeat_rate),
                    icon="bi-graph-up",
                ),
            ],
            "table": ReportTableData(
                title=str(_("Client activity")),
                subtitle=str(_("Daily new clients, appointments, repeat clients and messages.")),
                columns=[
                    TableColumn(key="day", label=str(_("Day")), bold=True),
                    TableColumn(key="new_clients", label=str(_("New clients")), align="right"),
                    TableColumn(key="active_clients", label=str(_("Active clients / bookings")), align="right"),
                    TableColumn(key="repeat_clients", label=str(_("Repeat clients")), align="right"),
                    TableColumn(key="messages", label=str(_("Messages")), align="right"),
                ],
                rows=rows,
                summary_row={
                    "day": str(_("Total")),
                    "new_clients": new_clients_total,
                    "active_clients": f"{active_clients_total} / {appointments_total}",
                    "repeat_clients": repeat_clients_total,
                    "messages": sum(messages_by_day.values()),
                },
                primary_summary=str(active_clients_total),
                secondary_summary=str(_("Active clients")),
                empty_message=str(_("No client activity for the selected period.")),
            ),
            "chart": ReportChartData(
                chart_id="lilyClientsActivityChart",
                title=str(_("Client activity")),
                labels=labels,
                type="line",
                icon="bi-people",
                datasets=[
                    ChartDatasetData(
                        label=str(_("New clients")),
                        data=cast("list[int | float | None]", new_client_values),
                        border_color=CLIENT_AXIS_COLOR,
                        background_color="rgba(249, 115, 22, 0.14)",
                        border_width=2,
                        point_radius=2,
                        tension=0.25,
                    ),
                    ChartDatasetData(
                        label=str(_("Appointments")),
                        data=cast("list[int | float | None]", appointment_values),
                        border_color=MONEY_AXIS_COLOR,
                        background_color="rgba(37, 99, 235, 0.10)",
                        border_width=2,
                        point_radius=2,
                        tension=0.25,
                    ),
                    ChartDatasetData(
                        label=str(_("Repeat clients")),
                        data=cast("list[int | float | None]", repeat_client_values),
                        border_color=SERVICE_AXIS_COLOR,
                        background_color="rgba(124, 58, 237, 0.10)",
                        border_width=2,
                        point_radius=2,
                        tension=0.25,
                    ),
                ],
            ),
        }
