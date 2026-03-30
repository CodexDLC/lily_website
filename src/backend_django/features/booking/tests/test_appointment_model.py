"""Tests for Appointment model methods and properties."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from features.booking.models.appointment import Appointment


@pytest.mark.unit
class TestAppointmentModelProperties:
    def test_datetime_end_property(self, pending_appointment):
        expected = pending_appointment.datetime_start + timedelta(minutes=pending_appointment.duration_minutes)
        assert pending_appointment.datetime_end == expected

    def test_is_upcoming_true_for_future(self, pending_appointment):
        assert pending_appointment.is_upcoming is True
        assert pending_appointment.is_past is False

    def test_is_past_true_for_past(self, client_obj, master, service):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() - timedelta(hours=2),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_COMPLETED,
        )
        assert apt.is_past is True
        assert apt.is_upcoming is False

    def test_is_today_property(self, client_obj, master, service):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() + timedelta(hours=1),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_PENDING,
        )
        assert apt.is_today is True

    def test_finalize_token_auto_generated(self, pending_appointment):
        assert pending_appointment.finalize_token is not None
        assert len(pending_appointment.finalize_token) > 10

    def test_price_auto_filled_from_service(self, client_obj, master, service):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() + timedelta(hours=48),
            duration_minutes=0,
            price=0,
            status=Appointment.STATUS_PENDING,
        )
        apt.refresh_from_db()
        # duration_minutes and price auto-filled from service in save()
        assert apt.duration_minutes == service.duration
        from decimal import Decimal

        assert apt.price == Decimal(str(service.price))

    def test_str_representation(self, pending_appointment):
        result = str(pending_appointment)
        assert pending_appointment.master.name in result


@pytest.mark.unit
class TestAppointmentCanCancel:
    def test_can_cancel_future_appointment(self, pending_appointment):
        assert pending_appointment.can_cancel() is True

    def test_cannot_cancel_within_2_hours(self, client_obj, master, service):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() + timedelta(hours=1),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_PENDING,
        )
        assert apt.can_cancel() is False

    def test_cannot_cancel_already_cancelled(self, client_obj, master, service):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() + timedelta(hours=48),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_CANCELLED,
        )
        assert apt.can_cancel() is False

    def test_cannot_cancel_completed(self, client_obj, master, service):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() - timedelta(hours=2),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_COMPLETED,
        )
        assert apt.can_cancel() is False


@pytest.mark.integration
class TestAppointmentCancel:
    def test_cancel_sets_status_and_fields(self, pending_appointment):
        pending_appointment.cancel(reason=Appointment.CANCEL_REASON_CLIENT, note="test note")
        pending_appointment.refresh_from_db()
        assert pending_appointment.status == Appointment.STATUS_CANCELLED
        assert pending_appointment.cancelled_at is not None
        assert pending_appointment.cancel_reason == Appointment.CANCEL_REASON_CLIENT
        assert pending_appointment.cancel_note == "test note"

    def test_cancel_raises_when_within_2_hours(self, client_obj, master, service):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() + timedelta(hours=1),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_PENDING,
        )
        with pytest.raises(ValidationError):
            apt.cancel()


@pytest.mark.integration
class TestAppointmentMarkCompleted:
    def test_mark_completed_from_confirmed(self, confirmed_appointment):
        confirmed_appointment.mark_completed()
        confirmed_appointment.refresh_from_db()
        assert confirmed_appointment.status == Appointment.STATUS_COMPLETED

    def test_mark_completed_raises_from_pending(self, pending_appointment):
        with pytest.raises(ValidationError):
            pending_appointment.mark_completed()

    def test_mark_completed_raises_from_cancelled(self, client_obj, master, service):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() + timedelta(hours=48),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_CANCELLED,
        )
        with pytest.raises(ValidationError):
            apt.mark_completed()


@pytest.mark.unit
class TestAppointmentCleanDoubleBooking:
    def test_clean_raises_on_double_booking(self, confirmed_appointment, client_obj, master, service):
        # Second appointment overlapping with confirmed_appointment
        conflicting = Appointment(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=confirmed_appointment.datetime_start + timedelta(minutes=30),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_PENDING,
        )
        with pytest.raises(ValidationError):
            conflicting.clean()

    def test_clean_passes_no_conflict(self, confirmed_appointment, client_obj, master, service):
        # Appointment after the first one ends
        non_conflicting = Appointment(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=confirmed_appointment.datetime_end + timedelta(minutes=10),
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_PENDING,
        )
        # Should not raise
        non_conflicting.clean()
