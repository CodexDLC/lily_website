"""Tests for DashboardView."""

import pytest
from django.test import Client as TestClient
from django.urls import reverse


@pytest.fixture
def http():
    return TestClient()


@pytest.mark.integration
class TestDashboardView:
    def test_anonymous_redirected(self, http):
        url = reverse("cabinet:dashboard")
        response = http.get(url)
        assert response.status_code == 302

    def test_non_staff_user_denied(self, http, master_user):
        http.force_login(master_user)
        url = reverse("cabinet:dashboard")
        response = http.get(url)
        # AdminRequiredMixin: non-staff gets PermissionDenied (403)
        assert response.status_code in (302, 403)

    def test_admin_sees_dashboard(self, http, admin_user):
        http.force_login(admin_user)
        url = reverse("cabinet:dashboard")
        response = http.get(url)
        assert response.status_code == 200

    def test_dashboard_context_has_pending_count(self, http, admin_user):
        http.force_login(admin_user)
        url = reverse("cabinet:dashboard")
        response = http.get(url)
        assert "pending_count" in response.context

    def test_dashboard_context_has_today_confirmed(self, http, admin_user):
        http.force_login(admin_user)
        url = reverse("cabinet:dashboard")
        response = http.get(url)
        assert "today_confirmed" in response.context

    def test_dashboard_pending_count_reflects_data(self, http, admin_user, pending_appointment):
        http.force_login(admin_user)
        url = reverse("cabinet:dashboard")
        response = http.get(url)
        assert response.context["pending_count"] >= 1
