import datetime as dt

import pytest
from django.utils import timezone
from features.booking.models import Appointment
from tests.factories.booking import AppointmentFactory


@pytest.mark.django_db
def test_complete_past_appointments_endpoint_completes_only_finished_confirmed_bookings(client, settings):
    settings.BOOKING_WORKER_API_KEY = "test-token"  # pragma: allowlist secret
    now = timezone.now()
    finished = AppointmentFactory(
        status=Appointment.STATUS_CONFIRMED,
        datetime_start=now - dt.timedelta(hours=2),
        duration_minutes=60,
    )
    still_running = AppointmentFactory(
        status=Appointment.STATUS_CONFIRMED,
        datetime_start=now - dt.timedelta(minutes=30),
        duration_minutes=60,
    )
    cancelled = AppointmentFactory(
        status=Appointment.STATUS_CANCELLED,
        datetime_start=now - dt.timedelta(hours=2),
        duration_minutes=60,
    )
    pending = AppointmentFactory(
        status=Appointment.STATUS_PENDING,
        datetime_start=now - dt.timedelta(hours=2),
        duration_minutes=60,
    )

    response = client.post(
        "/api/v1/booking/appointments/complete-past",
        **{
            "HTTP_X_INTERNAL_SCOPE": "booking.worker",
            "HTTP_X_INTERNAL_TOKEN": "test-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"success": True, "completed": 1}

    finished.refresh_from_db()
    still_running.refresh_from_db()
    cancelled.refresh_from_db()
    pending.refresh_from_db()
    assert finished.status == Appointment.STATUS_COMPLETED
    assert still_running.status == Appointment.STATUS_CONFIRMED
    assert cancelled.status == Appointment.STATUS_CANCELLED
    assert pending.status == Appointment.STATUS_PENDING


@pytest.mark.django_db
def test_complete_past_appointments_endpoint_is_idempotent(client, settings):
    settings.BOOKING_WORKER_API_KEY = "test-token"  # pragma: allowlist secret
    AppointmentFactory(
        status=Appointment.STATUS_CONFIRMED,
        datetime_start=timezone.now() - dt.timedelta(hours=2),
        duration_minutes=60,
    )
    headers = {
        "HTTP_X_INTERNAL_SCOPE": "booking.worker",
        "HTTP_X_INTERNAL_TOKEN": "test-token",
    }

    first = client.post("/api/v1/booking/appointments/complete-past", **headers)
    second = client.post("/api/v1/booking/appointments/complete-past", **headers)

    assert first.json()["completed"] == 1
    assert second.json()["completed"] == 0
