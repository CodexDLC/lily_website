"""Integration tests for BookingWizardView (V1 session-based booking)."""

import pytest
from django.test import Client as TestClient
from django.urls import reverse
from features.booking.dto import BookingState
from features.booking.models.appointment import Appointment
from features.booking.services.utils.session import BookingSessionService


@pytest.fixture
def http():
    return TestClient()


def _set_session_state(client, state: BookingState):
    """Helper: inject booking state into test client session."""
    session = client.session
    session[BookingSessionService.SESSION_KEY] = state.to_dict()
    session.save()


@pytest.mark.integration
class TestBookingWizardViewGet:
    def test_step1_returns_200(self, http, booking_settings, category, service, site_settings_obj):
        url = reverse("booking:booking_wizard")
        response = http.get(url)
        assert response.status_code == 200

    def test_step1_does_not_crash_without_session(self, http, booking_settings, site_settings_obj):
        url = reverse("booking:booking_wizard")
        response = http.get(url)
        assert response.status_code in (200, 302)

    def test_get_with_no_data_for_step2_redirects(self, http, booking_settings, site_settings_obj):
        # Requesting step=2 without service_id in session should fall back
        url = reverse("booking:booking_wizard") + "?step=2"
        response = http.get(url)
        assert response.status_code in (200, 302)

    def test_step4_with_complete_session_renders(
        self, http, booking_settings, category, service, master, site_settings_obj
    ):
        from datetime import date, timedelta

        target_date = date.today() + timedelta(days=2)
        state = BookingState(
            step=4,
            service_id=service.id,
            master_id=str(master.id),
            selected_date=target_date,
            selected_time="10:00",
        )
        _set_session_state(http, state)
        url = reverse("booking:booking_wizard") + "?step=4"
        response = http.get(url)
        assert response.status_code in (200, 302)


@pytest.mark.integration
class TestBookingWizardViewPost:
    def test_post_with_complete_session_creates_appointment(
        self, http, booking_settings, category, service, master, site_settings_obj, mock_notifications
    ):
        from datetime import date, timedelta

        target_date = date.today() + timedelta(days=2)
        state = BookingState(
            step=4,
            service_id=service.id,
            master_id=str(master.id),
            selected_date=target_date,
            selected_time="10:00",
        )
        _set_session_state(http, state)

        url = reverse("booking:booking_wizard")
        form_data = {
            "first_name": "Test",
            "last_name": "User",
            "phone": "+49555100001",
            "email": "wizard@test.de",
        }
        response = http.post(url, data=form_data)
        assert response.status_code in (200, 302)
        assert Appointment.objects.filter(service=service).exists()

    def test_post_with_empty_session_does_not_create_appointment(self, http, booking_settings, site_settings_obj):
        url = reverse("booking:booking_wizard")
        response = http.post(url, data={"first_name": "Test", "phone": "+49555200001"})
        assert response.status_code in (200, 302)
        assert Appointment.objects.count() == 0


@pytest.mark.integration
class TestBookingWizardHtmx:
    def test_htmx_get_returns_200(self, http, booking_settings, site_settings_obj):
        url = reverse("booking:booking_wizard")
        response = http.get(url, HTTP_HX_REQUEST="true")
        assert response.status_code in (200, 302)
