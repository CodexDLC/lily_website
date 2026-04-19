from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from codex_django.cabinet.selector.dashboard import DashboardSelector
from codex_django.cabinet.types.widgets import ListItem, ListWidgetData, MetricWidgetData
from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.http import HttpRequest


def _month_range() -> tuple[Any, Any]:
    now = timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _week_range() -> tuple[Any, Any]:
    now = timezone.now()
    return now - timedelta(days=6), now


@dataclass
class AnalyticsService:
    @staticmethod
    def get_kpi_metrics() -> dict[str, MetricWidgetData]:
        from features.booking.models import Appointment

        month_start, now = _month_range()
        prev_start = (month_start - timedelta(days=1)).replace(day=1)

        def _appt_qs(start: Any, end: Any):  # type: ignore[no-untyped-def]
            return Appointment.objects.filter(
                datetime_start__gte=start,
                datetime_start__lt=end,
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED],
            )

        this_month = _appt_qs(month_start, now)
        prev_month = _appt_qs(prev_start, month_start)

        _price = Coalesce("price_actual", "price", output_field=DecimalField())
        revenue = this_month.aggregate(total=Sum(_price))["total"] or 0
        prev_revenue = prev_month.aggregate(total=Sum(_price))["total"] or 0
        bookings = this_month.count()
        prev_bookings = prev_month.count()

        rev_trend = ""
        if prev_revenue:
            diff = ((revenue - prev_revenue) / prev_revenue) * 100
            rev_trend = f"{'+' if diff >= 0 else ''}{diff:.0f}%"

        bk_trend = ""
        if prev_bookings:
            diff = ((bookings - prev_bookings) / prev_bookings) * 100
            bk_trend = f"{'+' if diff >= 0 else ''}{diff:.0f}%"

        avg_check = (revenue / bookings) if bookings else 0

        from system.models.client import Client

        total_clients = Client.objects.exclude(status=Client.STATUS_BLOCKED).count()
        week_start = timezone.now() - timedelta(days=6)
        new_clients_week = (
            Client.objects.filter(created_at__gte=week_start).exclude(status=Client.STATUS_BLOCKED).count()
        )

        prev_avg = (prev_revenue / prev_bookings) if prev_bookings else 0
        if prev_avg:
            avg_diff = ((avg_check - prev_avg) / prev_avg) * 100
            avg_trend = f"{'+' if avg_diff >= 0 else ''}{avg_diff:.0f}%"
        else:
            avg_trend = ""

        _price_expr = Coalesce("price_actual", "price", output_field=DecimalField())
        total_appointments_alltime = Appointment.objects.count()
        total_revenue_alltime = (
            Appointment.objects.filter(
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED]
            ).aggregate(total=Sum(_price_expr))["total"]
            or 0
        )

        return {
            "revenue": MetricWidgetData(
                label=str(_("Monthly revenue")),
                value=f"{revenue:,.0f}".replace(",", " "),
                unit="€",
                trend_value=rev_trend,
                trend_label=str(_("vs last month")),
                trend_direction="up" if rev_trend.startswith("+") else "down",
                icon="bi-currency-euro",
                url=reverse_lazy("cabinet:analytics_reports") + "?tab=revenue",
            ),
            "bookings": MetricWidgetData(
                label=str(_("Monthly bookings")),
                value=str(bookings),
                trend_value=bk_trend,
                trend_label=str(_("vs last month")),
                trend_direction="up" if bk_trend.startswith("+") else "down",
                icon="bi-calendar-check",
                url=reverse_lazy("cabinet:analytics_reports") + "?tab=revenue",
            ),
            "clients": MetricWidgetData(
                label=str(_("Total clients")),
                value=str(total_clients),
                trend_value=f"+{new_clients_week}",
                trend_label=str(_("this week")),
                trend_direction="up",
                icon="bi-people",
                url=reverse_lazy("cabinet:analytics_reports") + "?tab=clients",
            ),
            "avg_check": MetricWidgetData(
                label=str(_("Average check")),
                value=f"{avg_check:,.0f}".replace(",", " "),
                unit="€",
                trend_value=avg_trend,
                trend_label=str(_("vs last month")),
                trend_direction="up" if avg_trend.startswith("+") else "down",
                icon="bi-receipt",
                url=reverse_lazy("cabinet:analytics_reports") + "?tab=revenue",
            ),
            "total_appointments": MetricWidgetData(
                label=str(_("Total appointments")),
                value=str(total_appointments_alltime),
                icon="bi-calendar2-check",
                url=reverse_lazy("cabinet:analytics_reports") + "?tab=revenue",
            ),
            "total_revenue": MetricWidgetData(
                label=str(_("Total revenue")),
                value=f"{total_revenue_alltime:,.0f}".replace(",", " "),
                unit="€",
                icon="bi-piggy-bank",
                url=reverse_lazy("cabinet:analytics_reports") + "?tab=revenue",
            ),
        }

    @staticmethod
    def get_chart_data() -> dict[str, dict[str, Any]]:
        from features.booking.models import Appointment

        _price = Coalesce("price_actual", "price", output_field=DecimalField())
        now = timezone.now()
        period_start = now - timedelta(days=29)

        # Daily data for last 30 days
        daily_qs = (
            Appointment.objects.filter(
                datetime_start__gte=period_start,
                datetime_start__lte=now,
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED],
            )
            .annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(total=Sum(_price))
            .order_by("day")
        )
        day_map: dict[str, float] = {row["day"].isoformat(): float(row["total"] or 0) for row in daily_qs}

        labels: list[str] = []
        values: list[float] = []
        for i in range(30):
            d = (period_start + timedelta(days=i)).date()
            labels.append(f"{d.day} {d.strftime('%b')}" if i % 5 == 0 else "")
            values.append(day_map.get(d.isoformat(), 0.0))

        # Trend: this month vs prev month
        month_start, _now = _month_range()
        prev_start = (month_start - timedelta(days=1)).replace(day=1)
        cur_month_rev = (
            Appointment.objects.filter(
                datetime_start__gte=month_start,
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED],
            ).aggregate(t=Sum(_price))["t"]
            or 0
        )
        prev_month_rev = (
            Appointment.objects.filter(
                datetime_start__gte=prev_start,
                datetime_start__lt=month_start,
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED],
            ).aggregate(t=Sum(_price))["t"]
            or 0
        )
        if prev_month_rev:
            diff = ((cur_month_rev - prev_month_rev) / prev_month_rev) * 100
            kpi_trend = f"{'+' if diff >= 0 else ''}{diff:.0f}%"
        else:
            kpi_trend = ""

        # Services donut: top 4 by appointment count
        top_services = (
            Appointment.objects.filter(status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED])
            .values("service__name")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")[:4]
        )
        donut_labels = [row["service__name"] for row in top_services]
        donut_data = [row["cnt"] for row in top_services]

        # Categories donut: top 5 by appointment count (ALL TIME)
        top_categories = (
            Appointment.objects.filter(status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED])
            .values("service__category__name")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")[:5]
        )
        cat_labels = [row["service__category__name"] or str(_("Other")) for row in top_categories]
        cat_data = [row["cnt"] for row in top_categories]

        return {
            "revenue_chart": {
                "chart_id": "revenueChart",
                "title": str(_("Revenue")),
                "subtitle": str(_("last 30 days")),
                "icon": "bi-graph-up",
                "type": "line",
                "kpi_value": f"€{cur_month_rev:,.0f}",
                "kpi_trend": kpi_trend,
                "kpi_trend_label": str(_("vs last month")),
                "datasets": [
                    {
                        "label": str(_("Revenue")),
                        "data": values,
                        "borderColor": "#4f46e5",
                        "backgroundColor": "rgba(79,70,229,0.08)",
                        "fill": True,
                        "tension": 0,
                        "borderWidth": 2,
                        "pointRadius": 0,
                        "pointHoverRadius": 4,
                        "pointBackgroundColor": "#fff",
                    }
                ],
                "chart_labels": labels,
            },
            "services_donut": {
                "chart_id": "servicesDonut",
                "title": str(_("Popular services")),
                "icon": "bi-pie-chart",
                "chart_labels": donut_labels,
                "chart_data": donut_data,
                "colors": ["#4f46e5", "#818cf8", "#c7d2fe", "#f1f5f9"],
            },
            "categories_donut": {
                "chart_id": "categoriesDonut",
                "title": str(_("Popular categories")),
                "subtitle": str(_("all time")),
                "icon": "bi-pie-chart-fill",
                "chart_labels": cat_labels,
                "chart_data": cat_data,
                "colors": ["#10b981", "#34d399", "#6ee7b7", "#a7f3d0", "#d1fae5"],
            },
        }

    @staticmethod
    def get_top_lists() -> dict[str, ListWidgetData]:
        from features.booking.models import Appointment

        month_start, now = _month_range()

        top_masters = (
            Appointment.objects.filter(
                datetime_start__gte=month_start,
                datetime_start__lte=now,
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED],
            )
            .values("master__name")
            .annotate(revenue=Sum(Coalesce("price_actual", "price", output_field=DecimalField())), cnt=Count("id"))
            .order_by("-revenue")[:5]
        )

        top_services = (
            Appointment.objects.filter(
                datetime_start__gte=month_start,
                datetime_start__lte=now,
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED],
            )
            .values("service__name")
            .annotate(revenue=Sum(Coalesce("price_actual", "price", output_field=DecimalField())), cnt=Count("id"))
            .order_by("-revenue")[:5]
        )

        def _initials(name: str) -> str:
            return "".join(p[0] for p in name.split() if p)[:2].upper()

        return {
            "top_masters": ListWidgetData(
                title=str(_("Top masters")),
                subtitle=str(_("this month")),
                icon="bi-star",
                items=[
                    ListItem(
                        label=row["master__name"] or "—",
                        value=f"€{row['revenue'] or 0:,.0f}",
                        avatar=_initials(row["master__name"] or ""),
                        sublabel=f"{row['cnt']} {_('bookings')}",
                    )
                    for row in top_masters
                ],
            ),
            "top_services": ListWidgetData(
                title=str(_("Top services")),
                subtitle=str(_("this month")),
                icon="bi-scissors",
                items=[
                    ListItem(
                        label=row["service__name"] or "—",
                        value=f"€{row['revenue'] or 0:,.0f}",
                        sublabel=f"{row['cnt']} {_('times')}",
                    )
                    for row in top_services
                ],
            ),
        }

    @staticmethod
    def get_reports_context(request: HttpRequest) -> dict[str, object]:
        from features.booking.models import Appointment

        tab = request.GET.get("tab", "revenue")
        active_period = request.GET.get("period", "month")

        now = timezone.now()
        if active_period == "week":
            period_start, period_end = _week_range()
        elif active_period == "quarter":
            period_start = now - timedelta(days=90)
            period_end = now
        else:
            period_start, period_end = _month_range()

        rows_qs = (
            Appointment.objects.filter(
                datetime_start__gte=period_start,
                datetime_start__lte=period_end,
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED],
            )
            .annotate(day=TruncDate("datetime_start"))
            .values("day")
            .annotate(revenue=Sum(Coalesce("price_actual", "price", output_field=DecimalField())), bookings=Count("id"))
            .order_by("day")
        )

        rows = [
            {
                "label": row["day"].strftime("%d.%m"),
                "revenue_fmt": f"€{row['revenue'] or 0:,.0f}",
                "bookings": row["bookings"],
                "conversion": "—",
            }
            for row in rows_qs
        ]

        total_revenue = sum(float(r["revenue"] or 0) for r in rows_qs)
        total_bookings = sum(r["bookings"] for r in rows_qs)

        from features.booking.models import Master

        staff_options = ["All team"] + list(
            Master.objects.filter(status=Master.STATUS_ACTIVE).values_list("name", flat=True)
        )

        report_tabs = [
            {"key": "revenue", "label": str(_("Revenue")), "icon": "bi-currency-euro"},
            {"key": "services", "label": str(_("Services")), "icon": "bi-scissors"},
            {"key": "masters", "label": str(_("Specialists")), "icon": "bi-people"},
        ]
        period_options = [
            {"key": "week", "label": str(_("Week"))},
            {"key": "month", "label": str(_("Month"))},
            {"key": "quarter", "label": str(_("Quarter"))},
        ]
        columns = [
            {"key": "label", "label": str(_("Period")), "bold": True},
            {"key": "revenue_fmt", "label": str(_("Revenue")), "align": "right"},
            {"key": "bookings", "label": str(_("Bookings")), "align": "right"},
            {"key": "conversion", "label": str(_("Conversion")), "align": "right"},
        ]
        summary_row = {
            "label": str(_("Total")),
            "revenue_fmt": f"€{total_revenue:,.0f}",
            "bookings": total_bookings,
            "conversion": "—",
        }
        chart_data = AnalyticsService.get_chart_data()
        return {
            "active_tab": tab,
            "active_period": active_period,
            "active_staff": request.GET.get("staff", ""),
            "report_title": str(_("Reports")),
            "report_summary": "",
            "period_label": str(_("Current reporting period")),
            "report_tabs": report_tabs,
            "period_options": period_options,
            "staff_options": staff_options,
            "columns": columns,
            "rows": rows,
            "summary_row": summary_row,
            "bar_max": max((r["revenue"] or 0 for r in rows_qs), default=1),
            "table_summary": {"total_revenue": summary_row["revenue_fmt"]},
            "revenue_chart_data": chart_data["revenue_chart"],
        }


# ── Register providers with DashboardSelector ─────────────────────────────────


@DashboardSelector.extend(cache_key="analytics_kpis", cache_ttl=300)  # type: ignore[untyped-decorator]
def provide_analytics_kpis(request: Any) -> Any:
    return AnalyticsService.get_kpi_metrics()


@DashboardSelector.extend(cache_key="analytics_charts", cache_ttl=300)  # type: ignore[untyped-decorator]
def provide_analytics_charts(request: Any) -> Any:
    return AnalyticsService.get_chart_data()


@DashboardSelector.extend(cache_key="analytics_lists", cache_ttl=300)  # type: ignore[untyped-decorator]
def provide_analytics_lists(request: Any) -> Any:
    return AnalyticsService.get_top_lists()
