from datetime import timedelta
from unittest.mock import patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone
from features.booking.models import Appointment

from lily_backend.cabinet.services.analytics import (
    AnalyticsService,
    _month_range,
    _week_range,
)
from lily_backend.cabinet.services.reports import LilyReportsService
from lily_backend.cabinet.views.analytics import (
    AnalyticsReportsView,
    analytics_dashboard_view,
)


@pytest.mark.django_db
class TestAnalyticsService:
    def test_month_range(self):
        start, end = _month_range()
        assert start.day == 1
        assert start.hour == 0
        assert end <= timezone.now()

    def test_week_range(self):
        start, end = _week_range()
        assert (end - start).days == 6

    def test_get_kpi_metrics_empty(self):
        """Test KPIs when no data exists."""
        metrics = AnalyticsService.get_kpi_metrics()
        assert metrics["revenue"].value == "0"
        assert metrics["bookings"].value == "0"
        assert metrics["clients"].value == "0"
        assert metrics["avg_check"].value == "0"

    def test_get_kpi_metrics_with_data(self, client_obj, master, service):
        """Test KPIs with current and previous month data."""
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_start = (month_start - timedelta(days=15)).replace(day=1)

        # This month
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=month_start + timedelta(hours=1),
            duration_minutes=30,
            price=100,
            status=Appointment.STATUS_CONFIRMED,
        )
        # Previous month
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=prev_month_start + timedelta(hours=1),
            duration_minutes=30,
            price=50,
            status=Appointment.STATUS_CONFIRMED,
        )

        metrics = AnalyticsService.get_kpi_metrics()
        assert metrics["revenue"].value == "100"
        assert metrics["revenue"].trend_value == "+100%"
        assert metrics["bookings"].value == "1"
        assert metrics["bookings"].trend_value == "+0%"  # 1 vs 1
        assert metrics["avg_check"].value == "100"

    def test_get_chart_data(self, client_obj, master, service):
        """Test 30-day revenue chart and donut data with trends."""
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_start = (month_start - timedelta(days=15)).replace(day=1)

        # Create appointment today
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=now - timedelta(hours=1),
            duration_minutes=30,
            price=100,
            status=Appointment.STATUS_COMPLETED,
        )
        # Create appointment in previous month for trend in chart
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=prev_month_start + timedelta(hours=1),
            duration_minutes=30,
            price=50,
            status=Appointment.STATUS_COMPLETED,
        )

        data = AnalyticsService.get_chart_data()
        assert "revenue_chart" in data
        assert data["revenue_chart"]["kpi_trend"] == "+100%"

        # Check values list has our 100
        values = data["revenue_chart"]["datasets"][0]["data"]
        assert 100.0 in values

    def test_dashboard_providers(self):
        """Test the registered dashboard providers."""
        from lily_backend.cabinet.services.analytics import (
            provide_analytics_charts,
            provide_analytics_kpis,
            provide_analytics_lists,
        )

        # We don't really care about 'request' here as the providers don't use it yet
        assert provide_analytics_kpis(None) is not None
        assert provide_analytics_charts(None) is not None
        assert provide_analytics_lists(None) is not None

    def test_get_top_lists(self, client_obj, master, service):
        """Test top masters and services lists."""
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now(),
            duration_minutes=30,
            price=100,
            status=Appointment.STATUS_CONFIRMED,
        )

        lists = AnalyticsService.get_top_lists()
        assert len(lists["top_masters"].items) == 1
        assert lists["top_masters"].items[0].label == "Test Master"
        assert lists["top_masters"].items[0].value == "€100"

        assert len(lists["top_services"].items) == 1
        assert lists["top_services"].items[0].label == "Test Service"

    def test_get_reports_context(self, client_obj, master, service):
        """Test report context for different tabs and periods."""
        rf = RequestFactory()

        # Create data for today
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now(),
            duration_minutes=30,
            price=100,
            status=Appointment.STATUS_CONFIRMED,
        )

        # Default (month)
        request = rf.get("/cabinet/reports/")
        context = AnalyticsService.get_reports_context(request)
        assert context["active_tab"] == "revenue"
        assert context["active_period"] == "month"
        assert context["summary_row"]["revenue_fmt"] == "€100"
        assert len(context["rows"]) >= 1

        # Week period
        request = rf.get("/cabinet/reports/", {"period": "week"})
        context = AnalyticsService.get_reports_context(request)
        assert context["active_period"] == "week"

        # Quarter period
        request = rf.get("/cabinet/reports/", {"period": "quarter"})
        context = AnalyticsService.get_reports_context(request)
        assert context["active_period"] == "quarter"

    def test_trend_calculation_edge_cases(self, client_obj, master, service):
        """Test trends when previous period had 0 data."""
        # Current month has data, prev has nothing
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now(),
            duration_minutes=30,
            price=100,
            status=Appointment.STATUS_CONFIRMED,
        )


class TestAnalyticsViews:
    def test_analytics_dashboard_view(self, rf, admin_user):
        """Test the dashboard wrapper view."""
        request = rf.get("/cabinet/analytics/")
        request.user = admin_user

        # Mock dashboard_view to avoid full rendering
        with (
            patch("lily_backend.cabinet.views.analytics.dashboard_view") as mock_dv,
            patch("lily_backend.cabinet.views.analytics.LilyReportsService.build"),
        ):
            mock_dv.return_value = HttpResponse("ok")
            response = analytics_dashboard_view(request)
            assert response.status_code == 200
            assert request.cabinet_module == "business_stats"

    def test_analytics_reports_view(self, rf, admin_user):
        """Test the reports template view."""
        request = rf.get("/cabinet/reports/")
        request.user = admin_user

        view = AnalyticsReportsView()
        view.request = request

        with patch("lily_backend.cabinet.views.analytics.LilyReportsService.build") as mock_build:
            mock_build.return_value = {}
            response = view.dispatch(request)
            assert response.status_code == 200
            assert request.cabinet_module == "business_stats"
            assert request.cabinet_space == "staff"

            context = view.get_context_data()
            assert "report" in context


@pytest.mark.django_db
class TestLilyReportsService:
    def test_reports_build_revenue(self, rf, client_obj, master, service):
        """Test building the revenue report via LilyReportsService."""
        # Create some data
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now(),
            duration_minutes=30,
            price=100,
            status=Appointment.STATUS_CONFIRMED,
        )

        request = rf.get("/cabinet/reports/", {"tab": "revenue", "period": "month"})
        report = LilyReportsService.build(request)

        assert report.active_tab == "revenue"
        assert len(report.summary_cards) > 0
        assert report.summary_cards[0].label == "Revenue"
        assert "€100" in report.summary_cards[0].value

    def test_reports_build_services(self, rf, client_obj, master, service):
        """Test building the services report."""
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now(),
            duration_minutes=30,
            price=100,
            status=Appointment.STATUS_CONFIRMED,
        )

        request = rf.get("/cabinet/reports/", {"tab": "services"})
        report = LilyReportsService.build(request)
        assert report.active_tab == "services"
        assert any(item for item in report.table.rows if item["service"] == "Test Service")

    def test_reports_build_clients(self, rf, client_obj, master, service):
        """Test building the clients report."""
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now(),
            duration_minutes=30,
            price=100,
            status=Appointment.STATUS_CONFIRMED,
        )

        request = rf.get("/cabinet/reports/", {"tab": "clients"})
        report = LilyReportsService.build(request)
        assert report.active_tab == "clients"
        assert len(report.table.rows) > 0

    def test_reports_invalid_tab_defaults_to_revenue(self, rf):
        request = rf.get("/cabinet/reports/", {"tab": "invalid"})
        report = LilyReportsService.build(request)
        assert report.active_tab == "revenue"
