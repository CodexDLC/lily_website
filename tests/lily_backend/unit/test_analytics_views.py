from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.urls import reverse

from src.lily_backend.cabinet.views.analytics import AnalyticsReportsView, analytics_dashboard_view


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def staff_user():
    user = MagicMock()
    user.is_active = True
    user.is_staff = True
    user.is_authenticated = True
    return user


def test_analytics_dashboard_view(rf, staff_user):
    url = reverse("cabinet:analytics_dashboard")
    request = rf.get(url)
    request.user = staff_user

    with patch("src.lily_backend.cabinet.views.analytics.dashboard_view") as mock_dashboard:
        mock_dashboard.return_value = MagicMock()
        analytics_dashboard_view(request)

    assert request.cabinet_module == "business_stats"
    mock_dashboard.assert_called_once_with(request)


def test_analytics_reports_view(rf, staff_user):
    url = reverse("cabinet:analytics_reports")
    request = rf.get(url)
    request.user = staff_user

    with patch("src.lily_backend.cabinet.views.analytics.LilyReportsService") as mock_service:
        mock_service.build.return_value = {"data": []}

        view = AnalyticsReportsView.as_view()
        response = view(request)

    assert response.status_code == 200
    assert request.cabinet_module == "business_stats"
    assert request.cabinet_space == "staff"
    mock_service.build.assert_called_once_with(request)
