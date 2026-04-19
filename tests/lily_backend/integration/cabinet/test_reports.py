from __future__ import annotations

from datetime import timedelta
from typing import Any, cast

from cabinet.services.reports import LilyReportsService
from cabinet.views.analytics import AnalyticsReportsView
from codex_django.cabinet import ReportChartData, ReportPageData, ReportTableData
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone
from features.booking.models import Appointment


def _request(path: str = "/cabinet/analytics/reports/", query: str = ""):
    return RequestFactory().get(f"{path}{query}")


def _appointment(client_obj, master, service, **kwargs):
    defaults = {
        "client": client_obj,
        "master": master,
        "service": service,
        "datetime_start": timezone.now(),
        "duration_minutes": service.duration,
        "price": service.price,
        "price_actual": service.price,
        "status": Appointment.STATUS_COMPLETED,
    }
    defaults.update(kwargs)
    return Appointment.objects.create(**defaults)


def test_reports_service_build_returns_page_data(confirmed_appointment):
    report = LilyReportsService.build(_request())

    assert isinstance(report, ReportPageData)
    assert report.active_tab == "revenue"
    assert report.active_period == "month"
    assert report.table.rows


def test_revenue_tab_uses_dual_axis_mixed_chart(confirmed_appointment):
    report = LilyReportsService.build(_request(query="?tab=revenue&period=week"))

    assert isinstance(report.chart, ReportChartData)
    assert report.chart.type == "bar"
    assert {cast("Any", dataset).y_axis_id for dataset in report.chart.datasets} == {"y", "y1"}
    assert {axis.id for axis in report.chart.axes} == {"y", "y1"}
    assert {cast("Any", dataset).type for dataset in report.chart.datasets} == {"bar", "line"}


def test_services_tab_contains_table_rows_and_summary(client_obj, master, service):
    _appointment(client_obj, master, service, price_actual="120.00")

    report = LilyReportsService.build(_request(query="?tab=services&period=month"))

    assert isinstance(report.table, ReportTableData)
    assert report.table.rows
    assert report.table.summary_row["bookings"] == 1
    assert report.table.summary_row["revenue"] == "€120"


def test_clients_tab_handles_empty_data():
    report = LilyReportsService.build(_request(query="?tab=clients&period=week"))

    assert isinstance(report, ReportPageData)
    assert report.active_tab == "clients"
    assert isinstance(report.table, ReportTableData)
    assert report.table.rows
    assert report.table.summary_row["new_clients"] == 0


def test_clients_tab_tracks_repeat_clients(client_obj, master, service):
    _appointment(
        client_obj,
        master,
        service,
        datetime_start=timezone.now() - timedelta(days=45),
        status=Appointment.STATUS_COMPLETED,
    )
    _appointment(client_obj, master, service)

    report = LilyReportsService.build(_request(query="?tab=clients&period=month"))

    assert report.table.summary_row["repeat_clients"] == 1


def test_reports_view_sets_cabinet_module_and_space():
    user = get_user_model().objects.create_user(
        username="staff-reports",
        email="staff-reports@test.local",
        password="test",  # pragma: allowlist secret
        is_staff=True,
    )
    request = _request()
    request.user = user

    response = AnalyticsReportsView.as_view()(request)

    assert response.status_code == 200
    assert request.cabinet_module == "business_stats"
    assert request.cabinet_space == "staff"
    assert response.template_name == ["cabinet/reports/page.html"]
