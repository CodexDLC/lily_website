"""Integration tests for BookingService (V1 booking flow)."""

from datetime import timedelta

import pytest
from django.utils import timezone
from features.booking.dto import BookingState
from features.booking.models.appointment import Appointment
from features.booking.models.client import Client
from features.booking.services.booking import BookingService


def _make_state(service_id, master_id, hours_ahead=48, time_str="10:00"):
    """Build a valid BookingState for tests."""
    target_dt = timezone.now() + timedelta(hours=hours_ahead)
    return BookingState(
        step=4,
        service_id=service_id,
        master_id=str(master_id),
        selected_date=target_dt.date(),
        selected_time=time_str,
    )


def _make_form_data(phone="+49500100001", email="booking@test.de"):
    return {
        "first_name": "Test",
        "last_name": "User",
        "phone": phone,
        "email": email,
        "consent_marketing": False,
    }


@pytest.mark.integration
class TestBookingServiceCreateAppointment:
    def test_creates_appointment_with_valid_state(self, service, master, booking_settings, mock_notifications):
        state = _make_state(service.id, master.id)
        result = BookingService.create_appointment(state, _make_form_data())
        assert result is not None
        assert isinstance(result, Appointment)
        assert result.status == Appointment.STATUS_PENDING
        assert result.service == service
        assert result.master == master

    def test_creates_client_if_not_exists(self, service, master, booking_settings, mock_notifications):
        state = _make_state(service.id, master.id)
        form = _make_form_data(phone="+49500200001", email="newclient@test.de")
        result = BookingService.create_appointment(state, form)
        assert result is not None
        assert Client.objects.filter(email="newclient@test.de").exists()

    def test_reuses_existing_client_by_email(self, client_obj, service, master, booking_settings, mock_notifications):
        # Use email lookup to bypass phone normalization differences
        state = _make_state(service.id, master.id)
        form = _make_form_data(phone="", email=client_obj.email)
        result = BookingService.create_appointment(state, form)
        assert result is not None
        assert result.client.email == client_obj.email
        assert Client.objects.filter(email=client_obj.email).count() == 1

    def test_returns_none_for_incomplete_state_missing_time(self, service, master, booking_settings):
        state = BookingState(step=3, service_id=service.id, master_id=str(master.id), selected_date=None)
        result = BookingService.create_appointment(state, _make_form_data())
        assert result is None

    def test_returns_none_for_missing_service(self, master, booking_settings):
        state = _make_state(service_id=99999, master_id=master.id)
        result = BookingService.create_appointment(state, _make_form_data())
        assert result is None

    def test_returns_none_for_missing_master(self, service, booking_settings):
        state = _make_state(service_id=service.id, master_id=99999)
        result = BookingService.create_appointment(state, _make_form_data())
        assert result is None

    def test_double_booking_prevented(self, service, master, booking_settings, mock_notifications):
        # Book master at 10:00 for 60 min
        state = _make_state(service.id, master.id)
        first = BookingService.create_appointment(state, _make_form_data(phone="+49500300001"))
        assert first is not None

        # Try to book same master at 10:30 (overlaps)
        state2 = _make_state(service.id, master.id, time_str="10:30")
        second = BookingService.create_appointment(state2, _make_form_data(phone="+49500400001"))
        assert second is None

    def test_notifications_called_after_creation(self, service, master, booking_settings, mock_notifications):
        state = _make_state(service.id, master.id)
        BookingService.create_appointment(state, _make_form_data(phone="+49500500001"))
        assert mock_notifications["send_booking_receipt"].called


@pytest.mark.integration
class TestBookingServiceAnyMaster:
    def test_any_master_creates_appointment(self, service, master, booking_settings, mock_notifications):
        state = _make_state(service.id, "any")
        result = BookingService.create_appointment(state, _make_form_data(phone="+49500600001"))
        assert result is not None
        assert result.master == master

    def test_any_master_returns_none_when_all_busy(self, service, master, booking_settings, mock_notifications):
        # Fill master's slot
        state1 = _make_state(service.id, "any")
        first = BookingService.create_appointment(state1, _make_form_data(phone="+49500700001"))
        assert first is not None

        # All masters busy now
        state2 = _make_state(service.id, "any", time_str="10:30")
        second = BookingService.create_appointment(state2, _make_form_data(phone="+49500800001"))
        assert second is None


@pytest.mark.unit
class TestBookingServiceIsSlotAvailable:
    def test_slot_is_available_on_empty_day(self, master, service):
        start_dt = timezone.now() + timedelta(hours=48)
        result = BookingService._is_slot_still_available(master, start_dt, service.duration)
        assert result is True

    def test_slot_not_available_when_overlap(self, client_obj, master, service):
        from features.booking.models.appointment import Appointment

        # Use noon explicitly to avoid midnight-boundary issues with timezone-aware date filtering.
        base = (timezone.now() + timedelta(hours=48)).replace(hour=12, minute=0, second=0, microsecond=0)
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=base,
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_CONFIRMED,
        )
        overlap_start = base + timedelta(minutes=30)
        result = BookingService._is_slot_still_available(master, overlap_start, service.duration)
        assert result is False

    def test_cancelled_appointment_does_not_block(self, client_obj, master, service, booking_settings):
        from features.booking.models.appointment import Appointment

        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() + timedelta(hours=48),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_CANCELLED,
        )
        result = BookingService._is_slot_still_available(master, apt.datetime_start, service.duration)
        assert result is True


@pytest.mark.unit
class TestBookingServiceFindFreeMaster:
    def test_finds_available_master(self, master, service, booking_settings):
        start_dt = timezone.now() + timedelta(hours=48)
        result = BookingService._find_free_master(service, start_dt)
        assert result == master

    def test_returns_none_when_all_busy(self, client_obj, master, service):
        from features.booking.models.appointment import Appointment

        # Use noon to avoid midnight-boundary issues with timezone-aware date filtering.
        base = (timezone.now() + timedelta(hours=48)).replace(hour=12, minute=0, second=0, microsecond=0)
        Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=base,
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_CONFIRMED,
        )
        overlap_start = base + timedelta(minutes=30)
        result = BookingService._find_free_master(service, overlap_start)
        assert result is None
