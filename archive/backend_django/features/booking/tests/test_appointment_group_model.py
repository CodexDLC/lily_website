"""Tests for AppointmentGroup and AppointmentGroupItem lifecycle methods."""

from datetime import timedelta

import pytest
from django.utils import timezone
from features.booking.models.appointment import Appointment
from features.booking.models.appointment_group import AppointmentGroup, AppointmentGroupItem


def _make_group_with_appointments(client_obj, master, service, count=2, status=Appointment.STATUS_PENDING):
    """Helper: creates group + N appointments + group items."""
    group = AppointmentGroup.objects.create(
        client=client_obj,
        booking_date=timezone.now().date() + timedelta(days=2),
        status=AppointmentGroup.STATUS_PENDING,
    )
    for i in range(count):
        apt = Appointment.objects.create(
            client=client_obj,
            master=master,
            service=service,
            datetime_start=timezone.now() + timedelta(hours=48, minutes=i * 60),
            duration_minutes=service.duration,
            price=service.price,
            status=status,
        )
        AppointmentGroupItem.objects.create(group=group, appointment=apt, service=service, order=i)
    return group


@pytest.mark.integration
class TestAppointmentGroupApproveAll:
    def test_approve_all_sets_group_confirmed(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service)
        group.approve_all()
        group.refresh_from_db()
        assert group.status == AppointmentGroup.STATUS_CONFIRMED

    def test_approve_all_confirms_pending_appointments(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service, count=2)
        group.approve_all()
        apt_ids = group.items.values_list("appointment_id", flat=True)
        statuses = set(Appointment.objects.filter(id__in=apt_ids).values_list("status", flat=True))
        assert statuses == {Appointment.STATUS_CONFIRMED}


@pytest.mark.integration
class TestAppointmentGroupCancelAll:
    def test_cancel_all_sets_group_cancelled(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service)
        group.cancel_all()
        group.refresh_from_db()
        assert group.status == AppointmentGroup.STATUS_CANCELLED

    def test_cancel_all_cancels_pending_appointments(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service)
        group.cancel_all()
        apt_ids = group.items.values_list("appointment_id", flat=True)
        statuses = set(Appointment.objects.filter(id__in=apt_ids).values_list("status", flat=True))
        assert statuses == {Appointment.STATUS_CANCELLED}

    def test_cancel_all_cancels_confirmed_appointments(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service, count=2, status=Appointment.STATUS_CONFIRMED)
        group.cancel_all()
        apt_ids = group.items.values_list("appointment_id", flat=True)
        statuses = set(Appointment.objects.filter(id__in=apt_ids).values_list("status", flat=True))
        assert statuses == {Appointment.STATUS_CANCELLED}

    def test_cancel_all_does_not_touch_already_completed(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service, count=1, status=Appointment.STATUS_COMPLETED)
        group.cancel_all()
        apt = group.items.first().appointment
        apt.refresh_from_db()
        assert apt.status == Appointment.STATUS_COMPLETED  # unchanged


@pytest.mark.integration
class TestAppointmentGroupCompleteAll:
    def test_complete_all_sets_group_completed(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service, count=1, status=Appointment.STATUS_CONFIRMED)
        group.complete_all()
        group.refresh_from_db()
        assert group.status == AppointmentGroup.STATUS_COMPLETED

    def test_complete_all_marks_confirmed_appointments(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service, count=2, status=Appointment.STATUS_CONFIRMED)
        group.complete_all()
        apt_ids = group.items.values_list("appointment_id", flat=True)
        statuses = set(Appointment.objects.filter(id__in=apt_ids).values_list("status", flat=True))
        assert statuses == {Appointment.STATUS_COMPLETED}

    def test_complete_all_ignores_pending_appointments(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service, count=1, status=Appointment.STATUS_PENDING)
        group.complete_all()
        apt = group.items.first().appointment
        apt.refresh_from_db()
        assert apt.status == Appointment.STATUS_PENDING  # unchanged


@pytest.mark.unit
class TestAppointmentGroupStr:
    def test_str_includes_pk_and_date(self, client_obj, master, service):
        group = _make_group_with_appointments(client_obj, master, service, count=1)
        result = str(group)
        assert str(group.pk) in result
