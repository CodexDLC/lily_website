"""Tests for SystemSettingsView."""

import pytest
from django.test import Client as TestClient
from django.urls import reverse


@pytest.fixture
def http():
    return TestClient()


@pytest.mark.integration
class TestSystemSettingsView:
    def test_anonymous_redirected(self, http):
        url = reverse("cabinet:system_settings")
        response = http.get(url)
        assert response.status_code in (302, 403)

    def test_non_staff_denied(self, http, master_user):
        http.force_login(master_user)
        url = reverse("cabinet:system_settings")
        response = http.get(url)
        assert response.status_code in (302, 403)

    def test_admin_sees_settings_page(self, http, admin_user, site_settings_obj, booking_settings):
        http.force_login(admin_user)
        url = reverse("cabinet:system_settings")
        response = http.get(url)
        assert response.status_code == 200

    def test_context_has_site_settings(self, http, admin_user, site_settings_obj, booking_settings):
        http.force_login(admin_user)
        url = reverse("cabinet:system_settings")
        response = http.get(url)
        assert "site_settings" in response.context

    def test_context_has_booking_settings(self, http, admin_user, site_settings_obj, booking_settings):
        http.force_login(admin_user)
        url = reverse("cabinet:system_settings")
        response = http.get(url)
        assert "booking_settings" in response.context

    def test_section_param_switches_tab(self, http, admin_user, site_settings_obj, booking_settings):
        http.force_login(admin_user)
        url = reverse("cabinet:system_settings") + "?section=booking"
        response = http.get(url)
        assert response.context["current_tab"] == "booking"

    def test_default_section_is_site(self, http, admin_user, site_settings_obj, booking_settings):
        http.force_login(admin_user)
        url = reverse("cabinet:system_settings")
        response = http.get(url)
        assert response.context["current_tab"] == "site"

    def test_htmx_post_returns_hx_refresh_header(self, http, admin_user, site_settings_obj, booking_settings):
        http.force_login(admin_user)
        url = reverse("cabinet:system_settings")
        response = http.post(
            url,
            data={"action": "save_site"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert response.get("HX-Refresh") == "true"

    def test_save_booking_updates_step_minutes(self, http, admin_user, site_settings_obj, booking_settings):
        from features.booking.models.booking_settings import BookingSettings

        http.force_login(admin_user)
        url = reverse("cabinet:system_settings")
        response = http.post(
            url,
            data={
                "action": "save_booking",
                "default_step_minutes": "15",
                "default_min_advance_minutes": "0",
                "default_max_advance_days": "60",
                "default_buffer_between_minutes": "0",
            },
        )
        assert response.status_code in (200, 302)
        updated = BookingSettings.load()
        assert updated.default_step_minutes == 15
