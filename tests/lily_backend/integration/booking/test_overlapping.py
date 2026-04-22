from datetime import date, datetime, time
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from features.booking.booking_settings import BookingSettings
from features.booking.models import Appointment, Master
from features.booking.providers.runtime import RuntimeBookingProvider
from features.main.models import Service, ServiceCategory


class BackToBackBookingTest(TestCase):
    def setUp(self):
        # Prevent Redis sync errors during tests
        self.patcher1 = patch("codex_django.system.mixins.settings.SiteSettingsSyncMixin.sync_to_redis", lambda x: None)
        self.patcher2 = patch(
            "codex_django.core.redis.managers.settings.DjangoSiteSettingsManager.save_instance", lambda x, y: None
        )
        self.patcher3 = patch(
            "codex_django.booking.mixins.settings.BookingSettingsSyncMixin.sync_booking_settings_to_redis",
            lambda x: None,
        )
        self.patcher1.start()
        self.patcher2.start()
        self.patcher3.start()

        self.category = ServiceCategory.objects.create(name="Test", slug="test")
        self.service = Service.objects.create(
            name="Service 30", slug="service-30", category=self.category, duration=30, price=100
        )
        self.master = Master.objects.create(name="Test Master", slug="test-master")
        self.provider = RuntimeBookingProvider()

        settings = BookingSettings.load()
        settings.step_minutes = 15
        for day_name in ("monday", "tuesday", "wednesday", "thursday", "friday"):
            setattr(settings, f"{day_name}_is_closed", False)
            setattr(settings, f"work_start_{day_name}", time(8, 0))
            setattr(settings, f"work_end_{day_name}", time(18, 0))
        settings.saturday_is_closed = False
        settings.work_start_saturday = time(8, 0)
        settings.work_end_saturday = time(18, 0)
        settings.sunday_is_closed = True
        settings.work_start_sunday = None
        settings.work_end_sunday = None
        settings.save()

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()

    def test_back_to_back_availability(self):
        booking_date = date(2026, 4, 20)  # Monday
        booking_date_str = booking_date.isoformat()

        start_time = timezone.make_aware(datetime.combine(booking_date, time(16, 0)))
        Appointment.objects.create(
            master=self.master,
            service=self.service,
            datetime_start=start_time,
            duration_minutes=30,
            status=Appointment.STATUS_CONFIRMED,
        )

        slots = self.provider.get_quick_create_slot_options(resource_id=self.master.id, booking_date=booking_date_str)

        self.assertIn(
            "16:30", slots, f"16:30 should be available after 16:00-16:30 appointment. Available slots: {slots}"
        )

    def test_appointment_creation_overlap(self):
        booking_date = date(2026, 4, 20)  # Monday

        Appointment.objects.create(
            master=self.master,
            service=self.service,
            datetime_start=timezone.make_aware(datetime.combine(booking_date, time(16, 0))),
            duration_minutes=30,
            status=Appointment.STATUS_CONFIRMED,
        )

        try:
            Appointment.objects.create(
                master=self.master,
                service=self.service,
                datetime_start=timezone.make_aware(datetime.combine(booking_date, time(16, 30))),
                duration_minutes=30,
                status=Appointment.STATUS_CONFIRMED,
            )
        except Exception as e:
            self.fail(f"Could not create back-to-back appointment: {e}")

    def test_service_duration_limit(self):
        settings = BookingSettings.load()
        for day_name in ("monday", "tuesday", "wednesday", "thursday", "friday"):
            setattr(settings, f"work_end_{day_name}", time(18, 0))
        settings.save()

        service_120 = Service.objects.create(
            name="Service 120", slug="service-120", category=self.category, duration=120, price=200
        )

        booking_date = date(2026, 4, 20)  # Monday
        from features.booking.selector.engine import get_booking_engine_gateway

        gateway = get_booking_engine_gateway()

        self.master.categories.add(self.category)
        from features.booking.models import MasterWorkingDay

        MasterWorkingDay.objects.create(
            master=self.master, weekday=booking_date.weekday(), start_time=time(8, 0), end_time=time(18, 0)
        )

        service_120.masters.add(self.master)

        slots = gateway.get_available_slots(service_ids=[service_120.id], target_date=booking_date)
        time_slots = slots.get_unique_start_times()

        self.assertIn("16:00", time_slots, f"16:00 should be the last slot for 2h service. Found: {time_slots}")
        self.assertNotIn("16:15", time_slots, "16:15 should be blocked for 2h service ending at 18:00")
        self.assertNotIn("18:30", time_slots, "18:30 should DEFINITELY be blocked")
