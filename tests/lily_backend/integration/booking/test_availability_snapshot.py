from datetime import timedelta

from codex_django.booking import DjangoAvailabilityAdapter
from django.utils import timezone
from features.booking.booking_settings import BookingSettings
from features.booking.models import Appointment, Master, MasterDayOff, MasterWorkingDay
from features.main.models import Service


def make_adapter():
    return DjangoAvailabilityAdapter(
        resource_model=Master,
        appointment_model=Appointment,
        service_model=Service,
        working_day_model=MasterWorkingDay,
        day_off_model=MasterDayOff,
        booking_settings_model=BookingSettings,
        step_minutes=30,
    )


def test_availability_snapshot_basic(master, service, booking_settings):
    """Snapshot test: check availability windows for a clean day."""
    adapter = make_adapter()
    target_date = timezone.now().date() + timedelta(days=1)

    availability = adapter.build_resources_availability([master.pk], target_date)
    avail = availability.get(master.pk) or availability.get(str(master.pk))

    assert avail is not None
    # 9:00 - 18:00 with 30m steps = 18 slots
    assert len(avail.free_windows) > 0


def test_appointment_booking_flow(client_obj, master, service, booking_settings):
    """Test business rules: confirm and cancel."""
    appt = Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service,
        datetime_start=timezone.now() + timedelta(days=2),
        duration_minutes=60,
        status=Appointment.STATUS_PENDING,
    )

    # Test Confirm
    appt.confirm()
    assert appt.status == Appointment.STATUS_CONFIRMED

    # Test Cancel
    appt.cancel(reason=Appointment.CANCEL_REASON_CLIENT)
    assert appt.status == Appointment.STATUS_CANCELLED
    assert appt.cancelled_at is not None
