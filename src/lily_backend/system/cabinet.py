from datetime import timedelta
from urllib.parse import urlencode

from codex_django.cabinet import (
    DashboardWidget,
    MetricWidgetData,
    SidebarItem,
    TopbarEntry,
    declare,
)
from codex_django.cabinet.selector.dashboard import DashboardSelector
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _


def _with_query(url: object, **params: str):
    return format_lazy("{}?{}", url, urlencode(params))


@DashboardSelector.extend(cache_key="user_summary", cache_ttl=0)  # type: ignore[untyped-decorator]
def provide_user_summary_kpi(request: HttpRequest) -> dict[str, MetricWidgetData]:
    from system.models.client import Client

    last_week = timezone.now() - timedelta(days=7)

    # Зарегистрированные = Client у которых есть User аккаунт (is_ghost=False)
    registered_count = Client.objects.filter(is_ghost=False).count()
    new_registered = Client.objects.filter(is_ghost=False, created_at__gte=last_week).count()

    return {
        "user_summary_kpi": MetricWidgetData(
            label=str(_("Registered users")),
            value=str(registered_count),
            trend_value=f"+{new_registered}",
            trend_direction="up",
            trend_label=str(_("this week")),
            icon="bi-person-check",
            url=reverse_lazy("cabinet:users_list"),
        )
    }


declare(
    module="analytics",
    space="staff",
    topbar=TopbarEntry(
        group="admin",
        label=_("Analytics"),
        icon="bi-graph-up",
        url=reverse_lazy("cabinet:analytics_dashboard"),
        order=10,
    ),
    sidebar=[
        SidebarItem(
            label=_("Dashboard"),
            url=reverse_lazy("cabinet:analytics_dashboard"),
            icon="bi-speedometer2",
            order=1,
        ),
    ],
    dashboard_widgets=[
        # ── Row 1: KPI карточки ──────────────────────────────
        DashboardWidget(template="cabinet/widgets/kpi.html", context_key="revenue", col="col-lg-3 col-md-6", order=10),
        DashboardWidget(template="cabinet/widgets/kpi.html", context_key="bookings", col="col-lg-3 col-md-6", order=11),
        DashboardWidget(template="cabinet/widgets/kpi.html", context_key="clients", col="col-lg-3 col-md-6", order=12),
        DashboardWidget(
            template="cabinet/widgets/kpi.html", context_key="avg_check", col="col-lg-3 col-md-6", order=13
        ),
        # ── Row 2: вторая строка KPI ─────────────────────────
        DashboardWidget(
            template="cabinet/widgets/kpi.html", context_key="user_summary_kpi", col="col-lg-3 col-md-6", order=14
        ),
        DashboardWidget(
            template="cabinet/widgets/kpi.html", context_key="conversations_stats", col="col-lg-3 col-md-6", order=15
        ),
        DashboardWidget(
            template="cabinet/widgets/kpi.html", context_key="total_appointments", col="col-lg-3 col-md-6", order=16
        ),
        DashboardWidget(
            template="cabinet/widgets/kpi.html", context_key="total_revenue", col="col-lg-3 col-md-6", order=17
        ),
        # ── Row 3: Чарт + Топ мастеров ──────────────────────
        DashboardWidget(template="cabinet/widgets/chart.html", context_key="revenue_chart", col="col-lg-8", order=20),
        DashboardWidget(template="cabinet/widgets/list.html", context_key="top_masters", col="col-lg-4", order=21),
        # ── Row 4: Топ услуг ─────────────────────────────────
        DashboardWidget(template="cabinet/widgets/list.html", context_key="top_services", col="col-lg-6", order=30),
    ],
)


declare(
    module="users",
    space="staff",
    topbar=TopbarEntry(
        group="admin",
        label=_("Users"),
        icon="bi-people",
        url=reverse_lazy("cabinet:users_list"),
        order=20,
    ),
    sidebar=[
        SidebarItem(
            label=_("All Users"),
            url=reverse_lazy("cabinet:users_list"),
            icon="bi-person-lines-fill",
            order=1,
        ),
        SidebarItem(
            label=_("Active Clients"),
            url=_with_query(reverse_lazy("cabinet:users_list"), segment="clients"),
            icon="bi-person-check",
            order=2,
        ),
        SidebarItem(
            label=_("Shadow Clients"),
            url=_with_query(reverse_lazy("cabinet:users_list"), segment="shadows"),
            icon="bi-snapchat",
            order=3,
        ),
        SidebarItem(
            label=_("Staff Only"),
            url=_with_query(reverse_lazy("cabinet:users_list"), segment="staff"),
            icon="bi-shield-lock",
            order=4,
        ),
    ],
)


# ── Client space (client-facing cabinet) ──────────────────────────────────────


def get_client_sidebar() -> list[SidebarItem]:
    return [
        SidebarItem(
            label=_("Home"),
            url=reverse_lazy("cabinet:client_home"),
            icon="bi-house-heart",
            order=1,
        ),
        SidebarItem(
            label=_("Appointments"),
            url=reverse_lazy("cabinet:client_appointments"),
            icon="bi-calendar2-heart",
            order=2,
        ),
        SidebarItem(
            label=_("Settings"),
            url=reverse_lazy("cabinet:settings"),
            icon="bi-gear",
            order=3,
        ),
    ]


declare(
    module="client",
    space="client",
    sidebar=get_client_sidebar(),
)

declare(
    module="client_settings",
    space="client",
    sidebar=get_client_sidebar(),
)
