from __future__ import annotations

import datetime as dt

from django.utils import timezone

from features.booking.models import Appointment


def complete_finished_confirmed_appointments(*, now: dt.datetime | None = None) -> int:
    """Complete confirmed appointments whose full service duration has elapsed."""
    cutoff = now or timezone.now()
    candidates = Appointment.objects.filter(
        status=Appointment.STATUS_CONFIRMED,
        datetime_start__lte=cutoff,
    ).values_list("id", "datetime_start", "duration_minutes")

    finished_ids = [
        appointment_id
        for appointment_id, datetime_start, duration_minutes in candidates
        if datetime_start + dt.timedelta(minutes=duration_minutes) <= cutoff
    ]
    if not finished_ids:
        return 0

    return Appointment.objects.filter(
        id__in=finished_ids,
        status=Appointment.STATUS_CONFIRMED,
    ).update(
        status=Appointment.STATUS_COMPLETED,
        updated_at=cutoff,
    )
