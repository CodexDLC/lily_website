import datetime as dt
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from features.booking.models import Appointment
from tests.factories.booking import AppointmentFactory


@pytest.mark.django_db
def test_schedule_booking_reminder_queues_versioned_deferred_job():
    from features.booking.services.reminders import schedule_booking_reminder

    now = timezone.now()
    appt = AppointmentFactory(
        status=Appointment.STATUS_CONFIRMED,
        datetime_start=now + dt.timedelta(hours=5),
        reminder_sent=False,
    )
    calls = []

    def enqueue_job(*args, **kwargs):
        calls.append((args, kwargs))
        return "job-1"

    job_id = schedule_booking_reminder(appt, enqueue_job=enqueue_job, now=now)

    assert job_id == "job-1"
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[0] == "send_booking_reminder_task"
    payload = args[1]
    assert payload["id"] == appt.pk
    assert payload["client_email"] == appt.client.email
    assert payload["requires_validation"] is True
    assert payload["mark_sent_on_success"] is True
    assert payload["expected_datetime_start"] == appt.datetime_start.isoformat()
    assert kwargs["_queue_name"] == "notifications"
    assert kwargs["_defer_until"] == appt.datetime_start - dt.timedelta(hours=2)
    assert kwargs["_job_id"] == f"reminder:{appt.pk}:{int(appt.datetime_start.timestamp())}"


@pytest.mark.django_db
def test_schedule_booking_reminder_skips_invalid_appointments():
    from features.booking.services.reminders import schedule_booking_reminder

    now = timezone.now()
    calls = []
    appt = AppointmentFactory(
        status=Appointment.STATUS_CANCELLED,
        datetime_start=now + dt.timedelta(hours=5),
        reminder_sent=False,
    )

    assert schedule_booking_reminder(appt, enqueue_job=lambda *a, **kw: calls.append((a, kw)), now=now) is None
    assert calls == []


@pytest.mark.django_db
def test_reminder_payload_endpoint_rejects_stale_or_cancelled_jobs(client, confirmed_appointment, settings):
    settings.BOOKING_WORKER_API_KEY = "test-token"  # pragma: allowlist secret
    expected_start = confirmed_appointment.datetime_start.isoformat()
    headers = {
        "HTTP_X_INTERNAL_SCOPE": "booking.worker",
        "HTTP_X_INTERNAL_TOKEN": "test-token",
    }

    response = client.get(
        f"/api/v1/booking/appointments/{confirmed_appointment.pk}/reminder-payload",
        {"expected_datetime_start": expected_start},
        **headers,
    )

    assert response.status_code == 200
    assert response.json()["send"] is True

    confirmed_appointment.status = Appointment.STATUS_CANCELLED
    confirmed_appointment.save(update_fields=["status", "updated_at"])

    response = client.get(
        f"/api/v1/booking/appointments/{confirmed_appointment.pk}/reminder-payload",
        {"expected_datetime_start": expected_start},
        **headers,
    )

    assert response.status_code == 200
    assert response.json() == {"send": False}


@pytest.mark.django_db
def test_confirmed_appointment_schedules_reminder(monkeypatch):
    from features.booking.services import reminders

    appt = AppointmentFactory(status=Appointment.STATUS_PENDING)
    scheduled = []

    def fake_schedule(appointment):
        scheduled.append(appointment.pk)
        return "job-1"

    monkeypatch.setattr(reminders, "schedule_booking_reminder", fake_schedule)

    with patch("features.conversations.services.notifications._get_engine") as get_engine:
        get_engine.return_value = MagicMock()
        appt.confirm()

    assert scheduled == [appt.pk]
