"""
Stage 6.2 — Smoke tests for DjangoAvailabilityAdapter with lily_backend models.

Verifies that the adapter wires up correctly to our ORM and returns
sensible availability data. Based on test_dirty_seconds from backend_django.
"""

from __future__ import annotations

import datetime

from codex_django.booking import DjangoAvailabilityAdapter
from django.utils import timezone
from features.booking.booking_settings import BookingSettings
from features.booking.models import Appointment, Master, MasterDayOff, MasterWorkingDay
from features.main.models import Service

# ---------------------------------------------------------------------------
# Adapter factory
# ---------------------------------------------------------------------------


def make_adapter(**kwargs) -> DjangoAvailabilityAdapter:
    defaults = dict(
        resource_model=Master,
        appointment_model=Appointment,
        service_model=Service,
        working_day_model=MasterWorkingDay,
        day_off_model=MasterDayOff,
        booking_settings_model=BookingSettings,
        step_minutes=30,
    )
    defaults.update(kwargs)
    return DjangoAvailabilityAdapter(**defaults)


# ---------------------------------------------------------------------------
# Basic smoke
# ---------------------------------------------------------------------------


def test_adapter_returns_availability_for_active_master(master, booking_settings):
    """Adapter builds availability for a working master with no appointments."""
    adapter = make_adapter()
    target_date = _next_weekday(0)  # nearest Monday

    availability = adapter.build_resources_availability([master.pk], target_date)

    assert master.pk in availability or str(master.pk) in availability
    avail = availability.get(master.pk) or availability.get(str(master.pk))
    assert avail is not None
    assert len(avail.free_windows) > 0


def test_work_days_property_populated_from_working_days(booking_settings, category):
    """work_days property correctly returns weekday indices from MasterWorkingDay records."""
    m = Master.objects.create(
        name="Weekday Master",
        slug="weekday-master",
        status=Master.STATUS_ACTIVE,
        work_start=datetime.time(9, 0),
        work_end=datetime.time(17, 0),
    )
    for weekday in range(5):  # Mon=0 … Fri=4 only
        MasterWorkingDay.objects.create(
            master=m,
            weekday=weekday,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
        )

    # work_days property must reflect only Mon-Fri
    assert m.work_days == [0, 1, 2, 3, 4]
    assert 5 not in m.work_days  # Saturday not in work_days
    assert 6 not in m.work_days  # Sunday not in work_days


def test_confirmed_appointment_blocks_slots(master, client_obj, service, booking_settings):
    """Confirmed appointment blocks the corresponding time window."""
    target_date = _next_weekday(0)
    appt_start = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time(10, 0)))
    Appointment.objects.create(
        master=master,
        service=service,
        client=client_obj,
        datetime_start=appt_start,
        duration_minutes=60,
        status=Appointment.STATUS_CONFIRMED,
    )

    adapter = make_adapter()
    availability = adapter.build_resources_availability([master.pk], target_date)
    avail = availability.get(master.pk) or availability.get(str(master.pk))

    assert avail is not None
    # 10:00-11:00 must be absent from free windows
    for start, _ in avail.free_windows:
        assert not (start.hour == 10 and start.minute == 0)


def test_day_off_returns_no_availability(master, booking_settings):
    """MasterDayOff blocks the entire day."""
    target_date = _next_weekday(1)  # Tuesday
    MasterDayOff.objects.create(master=master, date=target_date)

    adapter = make_adapter()
    availability = adapter.build_resources_availability([master.pk], target_date)
    avail = availability.get(master.pk) or availability.get(str(master.pk))

    assert avail is None or len(avail.free_windows) == 0


def test_dirty_seconds_cleaned_by_adapter(master, client_obj, service, booking_settings):
    """Microseconds in appointment datetime_start are stripped — no micro-gaps."""
    target_date = _next_weekday(2)  # Wednesday
    dirty_start = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time(10, 0, 0, 123456)))

    Appointment.objects.create(
        master=master,
        service=service,
        client=client_obj,
        datetime_start=dirty_start,
        duration_minutes=60,
        status=Appointment.STATUS_CONFIRMED,
    )

    adapter = make_adapter()
    availability = adapter.build_resources_availability([master.pk], target_date)
    avail = availability.get(master.pk) or availability.get(str(master.pk))

    assert avail is not None
    for start, _end in avail.free_windows:
        assert start.microsecond == 0
        assert _end.microsecond == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _next_weekday(weekday: int) -> datetime.date:
    """Return the nearest future date with the given weekday (0=Mon … 6=Sun)."""
    today = datetime.date.today()
    days_ahead = (weekday - today.weekday() + 7) % 7 or 7
    return today + datetime.timedelta(days=days_ahead)
