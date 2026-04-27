from django.test import override_settings
from features.booking.models import Appointment

_HEADERS = {
    "HTTP_X_INTERNAL_SCOPE": "booking.worker",
    "HTTP_X_INTERNAL_TOKEN": "test-booking-token",
}


@override_settings(BOOKING_WORKER_API_KEY="test-booking-token")  # pragma: allowlist secret
def test_bot_api_upcoming(client, confirmed_appointment):
    """Test /api/v1/booking/appointments/upcoming endpoint."""
    response = client.get("/api/v1/booking/appointments/upcoming", **_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["id"] == confirmed_appointment.id


@override_settings(BOOKING_WORKER_API_KEY="test-booking-token")  # pragma: allowlist secret
def test_bot_api_no_show(client, confirmed_appointment):
    """Test /api/v1/booking/appointments/{id}/no-show endpoint."""
    url = f"/api/v1/booking/appointments/{confirmed_appointment.id}/no-show"
    response = client.post(url, **_HEADERS)
    assert response.status_code == 200

    confirmed_appointment.refresh_from_db()
    assert confirmed_appointment.status == Appointment.STATUS_NO_SHOW


@override_settings(BOOKING_WORKER_API_KEY="test-booking-token")  # pragma: allowlist secret
def test_bot_api_reschedule_proposal(client, confirmed_appointment):
    """Test /api/v1/booking/appointments/{id}/propose-reschedule endpoint."""
    url = f"/api/v1/booking/appointments/{confirmed_appointment.id}/propose-reschedule"
    payload = {"proposed_datetime_str": "20.10.2026 15:00"}
    response = client.post(url, data=payload, content_type="application/json", **_HEADERS)
    assert response.status_code == 200

    confirmed_appointment.refresh_from_db()
    assert confirmed_appointment.status == Appointment.STATUS_RESCHEDULE_PROPOSED
