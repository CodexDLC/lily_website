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

        # Ensure 15 min step
        settings = BookingSettings.load()
        settings.step_minutes = 15
        settings.save()

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()

    def test_back_to_back_availability(self):
        # 1. Create appointment 16:00 - 16:30 for Client A
        booking_date = date.today()
        # Today's date for provider
        booking_date_str = booking_date.isoformat()

        start_time = timezone.make_aware(datetime.combine(booking_date, time(16, 0)))
        Appointment.objects.create(
            master=self.master,
            service=self.service,
            datetime_start=start_time,
            duration_minutes=30,
            status=Appointment.STATUS_CONFIRMED,
        )

        # 2. Check slots at 16:30 for Client B
        slots = self.provider.get_quick_create_slot_options(resource_id=self.master.id, booking_date=booking_date_str)

        # 16:30 should be in slots
        self.assertIn(
            "16:30", slots, f"16:30 should be available after 16:00-16:30 appointment. Available slots: {slots}"
        )

    def test_appointment_creation_overlap(self):
        # Even if we don't have a special validation in the model,
        # let's see if the provider can create it.
        booking_date = date.today()

        # 1. First appointment 16:00 - 16:30
        Appointment.objects.create(
            master=self.master,
            service=self.service,
            datetime_start=timezone.make_aware(datetime.combine(booking_date, time(16, 0))),
            duration_minutes=30,
            status=Appointment.STATUS_CONFIRMED,
        )

        # 2. Try to create second via quick-create or direct model
        # The user says "forced to create manually" - maybe our quick-create has a check?
        # Let's check RuntimeBookingProvider.create_quick_appointment (if it exists)

        # We'll just check if a second one can exist at 16:30
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
        # Work ends at 18:00 (already set in align or setUp)
        settings = BookingSettings.load()
        settings.work_end_weekdays = time(18, 0)
        settings.save()

        # Service duration = 120 mins (2 hours)
        service_120 = Service.objects.create(
            name="Service 120", slug="service-120", category=self.category, duration=120, price=200
        )

        booking_date = date.today()
        # Get slots via the actual engine gateway (like the public site does)
        from features.booking.selector.engine import get_booking_engine_gateway

        gateway = get_booking_engine_gateway()

        # 3. Add master to category and create schedule (required by engine adapter)
        self.master.categories.add(self.category)
        from ..models import MasterWorkingDay

        MasterWorkingDay.objects.create(
            master=self.master, weekday=booking_date.weekday(), start_time=time(8, 0), end_time=time(18, 0)
        )

        # We need to ensure the master is active and assigned to service
        service_120.masters.add(self.master)

        slots = gateway.get_available_slots(service_ids=[service_120.id], target_date=booking_date)

        # With 18:00 end and 120min duration, 16:00 is the LAST possible start.
        # 16:15, 16:30, etc. should NOT be there.
        time_slots = slots.get_unique_start_times()

        self.assertIn("16:00", time_slots, f"16:00 should be the last slot for 2h service. Found: {time_slots}")
        self.assertNotIn("16:15", time_slots, "16:15 should be blocked for 2h service ending at 18:00")
        self.assertNotIn("18:30", time_slots, "18:30 should DEFINITELY be blocked")
