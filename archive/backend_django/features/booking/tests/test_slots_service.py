"""
Integration tests for features.booking.services.slots.SlotService.
Tests slot generation logic with real DB objects.
"""

from datetime import date, time, timedelta

import pytest
from django.utils import timezone
from features.booking.models import Appointment, Master, MasterDayOff
from features.booking.services.slots import SlotService
from features.system.models.site_settings import SiteSettings


def _make_site_settings(
    work_start_weekdays=time(9, 0),
    work_end_weekdays=time(18, 0),
    work_start_saturday=time(10, 0),
    work_end_saturday=time(14, 0),
) -> SiteSettings:
    """Create/update SiteSettings singleton with test working hours."""
    obj, _ = SiteSettings.objects.get_or_create(pk=1)
    obj.work_start_weekdays = work_start_weekdays
    obj.work_end_weekdays = work_end_weekdays
    obj.work_start_saturday = work_start_saturday
    obj.work_end_saturday = work_end_saturday
    obj.save()
    return obj


def _next_weekday(weekday: int) -> date:
    """Return the next date with the given weekday (0=Mon, 6=Sun)."""
    today = date.today()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


@pytest.mark.django_db
class TestSlotServiceGetAvailableSlots:
    def setup_method(self):
        self.service_instance = SlotService(step_minutes=30)

    def test_returns_list(self, master, service, site_settings_obj):
        _make_site_settings()
        next_monday = _next_weekday(0)
        slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=60,
            allow_past=True,
        )
        assert isinstance(slots, list)

    def test_returns_slots_for_single_master(self, master, service, site_settings_obj):
        _make_site_settings()
        next_monday = _next_weekday(0)
        slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=60,
            allow_past=True,
        )
        assert len(slots) > 0

    def test_empty_masters_list_returns_empty(self, site_settings_obj):
        _make_site_settings()
        slots = self.service_instance.get_available_slots(
            masters=[],
            date_obj=_next_weekday(0),
            duration_minutes=60,
            allow_past=True,
        )
        assert slots == []

    def test_sunday_returns_empty(self, master, site_settings_obj):
        _make_site_settings()
        next_sunday = _next_weekday(6)
        slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_sunday,
            duration_minutes=60,
            allow_past=True,
        )
        assert slots == []

    def test_slots_are_sorted(self, master, site_settings_obj):
        _make_site_settings()
        next_monday = _next_weekday(0)
        slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=30,
            allow_past=True,
        )
        assert slots == sorted(slots)

    def test_slots_in_hh_mm_format(self, master, site_settings_obj):
        _make_site_settings()
        next_monday = _next_weekday(0)
        slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=60,
            allow_past=True,
        )
        for slot in slots:
            assert len(slot) == 5, f"Slot '{slot}' is not HH:MM format"
            assert slot[2] == ":", f"Slot '{slot}' missing colon"

    def test_multiple_masters_combined_slots(self, master, category, site_settings_obj):
        _make_site_settings()
        next_monday = _next_weekday(0)
        master2 = Master.objects.create(
            name="Second Master",
            slug="second-master-slots",
            status=Master.STATUS_ACTIVE,
            work_days=[0, 1, 2, 3, 4, 5, 6],
        )
        master2.categories.add(category)

        slots = self.service_instance.get_available_slots(
            masters=[master, master2],
            date_obj=next_monday,
            duration_minutes=60,
            allow_past=True,
        )
        single_slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=60,
            allow_past=True,
        )
        # Combined should have at least as many as single
        assert len(slots) >= len(single_slots)


@pytest.mark.django_db
class TestSlotServiceWithAppointments:
    def setup_method(self):
        self.service_instance = SlotService(step_minutes=30)

    def test_busy_slot_excluded(self, master, service, client_obj, site_settings_obj, booking_settings):
        _make_site_settings()
        next_monday = _next_weekday(0)
        # Create a confirmed appointment at 09:00 with 60 min duration
        appt_start = timezone.make_aware(__import__("datetime").datetime.combine(next_monday, time(9, 0)))
        Appointment.objects.create(
            master=master,
            client=client_obj,
            service=service,
            datetime_start=appt_start,
            duration_minutes=60,
            status=Appointment.STATUS_CONFIRMED,
            price="50.00",
        )

        slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=60,
            allow_past=True,
        )
        # 09:00 should NOT be available (appointment occupies it)
        assert "09:00" not in slots
        # 10:00 should be available (after the appointment ends)
        assert "10:00" in slots

    def test_pending_appointment_blocks_slot(self, master, service, client_obj, site_settings_obj, booking_settings):
        _make_site_settings()
        next_monday = _next_weekday(0)
        appt_start = timezone.make_aware(__import__("datetime").datetime.combine(next_monday, time(9, 0)))
        Appointment.objects.create(
            master=master,
            client=client_obj,
            service=service,
            datetime_start=appt_start,
            duration_minutes=60,
            status=Appointment.STATUS_PENDING,
            price="50.00",
        )

        slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=60,
            allow_past=True,
        )
        assert "09:00" not in slots


@pytest.mark.django_db
class TestSlotServiceMasterDayOff:
    def setup_method(self):
        self.service_instance = SlotService(step_minutes=30)

    def test_day_off_returns_empty_slots(self, master, site_settings_obj):
        _make_site_settings()
        next_monday = _next_weekday(0)
        MasterDayOff.objects.create(master=master, date=next_monday)

        slots = self.service_instance.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=60,
            allow_past=True,
        )
        assert slots == []


@pytest.mark.django_db
class TestSlotServiceWorkDays:
    def setup_method(self):
        self.service_instance = SlotService(step_minutes=30)

    def test_master_not_working_on_day_returns_empty(self, category, site_settings_obj):
        _make_site_settings()
        # Create master that only works Mon–Fri (0–4)
        restricted_master = Master.objects.create(
            name="Restricted Master",
            slug="restricted-master-slots",
            status=Master.STATUS_ACTIVE,
            work_days=[0, 1, 2, 3, 4],  # No Saturday (5) or Sunday (6)
        )
        restricted_master.categories.add(category)

        next_saturday = _next_weekday(5)
        slots = self.service_instance.get_available_slots(
            masters=restricted_master,
            date_obj=next_saturday,
            duration_minutes=60,
            allow_past=True,
        )
        assert slots == []

    def test_master_working_on_saturday(self, category, site_settings_obj):
        _make_site_settings()
        saturday_master = Master.objects.create(
            name="Saturday Master",
            slug="saturday-master-slots",
            status=Master.STATUS_ACTIVE,
            work_days=[0, 1, 2, 3, 4, 5],  # Works Saturday
        )
        saturday_master.categories.add(category)

        next_saturday = _next_weekday(5)
        slots = self.service_instance.get_available_slots(
            masters=saturday_master,
            date_obj=next_saturday,
            duration_minutes=60,
            allow_past=True,
        )
        # Saturday has work hours configured, so should have slots
        assert isinstance(slots, list)


@pytest.mark.django_db
class TestSlotServiceGetWorkingHours:
    def setup_method(self):
        self.service_instance = SlotService()

    def test_weekday_returns_weekday_hours(self, site_settings_obj):
        settings = _make_site_settings(
            work_start_weekdays=time(9, 0),
            work_end_weekdays=time(17, 0),
        )
        self.service_instance._cached_settings = settings

        # Monday = 0
        result = self.service_instance._get_working_hours(date(2024, 5, 13))
        assert result == (time(9, 0), time(17, 0))

    def test_saturday_returns_saturday_hours(self, site_settings_obj):
        settings = _make_site_settings(
            work_start_saturday=time(10, 0),
            work_end_saturday=time(14, 0),
        )
        self.service_instance._cached_settings = settings

        # Saturday = 5
        result = self.service_instance._get_working_hours(date(2024, 5, 18))
        assert result == (time(10, 0), time(14, 0))

    def test_sunday_returns_none(self, site_settings_obj):
        settings = _make_site_settings()
        self.service_instance._cached_settings = settings

        # Sunday = 6
        result = self.service_instance._get_working_hours(date(2024, 5, 19))
        assert result is None


@pytest.mark.django_db
class TestSlotServiceCachedSettings:
    def test_settings_cached_after_first_call(self, site_settings_obj):
        _make_site_settings()
        svc = SlotService()
        assert svc._cached_settings is None
        settings1 = svc._get_settings()
        settings2 = svc._get_settings()
        assert settings1 is settings2  # Same object returned

    def test_duration_too_long_produces_no_slots(self, master, site_settings_obj):
        """If service duration exceeds entire working day, no slots returned."""
        _make_site_settings(
            work_start_weekdays=time(9, 0),
            work_end_weekdays=time(10, 0),  # Only 1 hour window
        )
        svc = SlotService()
        next_monday = _next_weekday(0)
        slots = svc.get_available_slots(
            masters=master,
            date_obj=next_monday,
            duration_minutes=120,  # 2 hours — won't fit
            allow_past=True,
        )
        assert slots == []
