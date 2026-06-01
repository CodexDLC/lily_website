from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

from asgiref.sync import async_to_sync
from core.arq.client import DjangoArqClient
from django.utils import timezone

from features.booking.models import Appointment

if TYPE_CHECKING:
    from collections.abc import Callable

REMINDER_LEAD_TIME = dt.timedelta(hours=2)
REMINDER_QUEUE = "notifications"
REMINDER_TASK = "send_booking_reminder_task"


def build_reminder_payload(appt: Appointment) -> dict[str, Any]:
    local_start = timezone.localtime(appt.datetime_start)
    return {
        "id": appt.pk,
        "client_email": appt.client.email if appt.client else "",
        "name": appt.client.first_name if appt.client else "",
        "service_name": appt.service.name,
        "datetime": local_start.strftime("%d.%m.%Y %H:%M"),
        "lang": appt.lang or "de",
        "master_name": appt.master.name,
    }


def build_scheduled_reminder_payload(appt: Appointment) -> dict[str, Any]:
    payload = build_reminder_payload(appt)
    payload.update(
        {
            "requires_validation": True,
            "mark_sent_on_success": True,
            "expected_datetime_start": appt.datetime_start.isoformat(),
        }
    )
    return payload


def reminder_job_id(appt: Appointment) -> str:
    return f"reminder:{appt.pk}:{int(appt.datetime_start.timestamp())}"


def schedule_booking_reminder(
    appt: Appointment,
    *,
    enqueue_job: Callable[..., Any] | None = None,
    now: dt.datetime | None = None,
) -> str | None:
    if not _can_schedule_reminder(appt, now=now):
        return None

    enqueue = enqueue_job or _enqueue_job_sync
    defer_until = appt.datetime_start - REMINDER_LEAD_TIME
    kwargs: dict[str, Any] = {
        "_queue_name": REMINDER_QUEUE,
        "_job_id": reminder_job_id(appt),
    }
    if defer_until > (now or timezone.now()):
        kwargs["_defer_until"] = defer_until

    job = enqueue(REMINDER_TASK, build_scheduled_reminder_payload(appt), **kwargs)
    return str(getattr(job, "job_id", job)) if job else None


def should_send_reminder(appt: Appointment, *, expected_datetime_start: str | None = None) -> bool:
    if not _can_schedule_reminder(appt):
        return False
    return not expected_datetime_start or appt.datetime_start.isoformat() == expected_datetime_start


def _can_schedule_reminder(appt: Appointment, *, now: dt.datetime | None = None) -> bool:
    current_time = now or timezone.now()
    return (
        appt.pk is not None
        and appt.status == Appointment.STATUS_CONFIRMED
        and not appt.reminder_sent
        and bool(appt.client and appt.client.email)
        and appt.datetime_start > current_time
    )


def _enqueue_job_sync(*args: Any, **kwargs: Any) -> Any:
    return async_to_sync(DjangoArqClient.enqueue_job)(*args, **kwargs)
