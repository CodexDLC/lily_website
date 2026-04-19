from datetime import timedelta
from unittest.mock import MagicMock, call, patch

import pytest
from django.urls import reverse
from django.utils import timezone
from features.booking.dto.public_cart import PublicCart, PublicCartItem
from features.booking.models import Appointment
from features.booking.services.notifications import (
    handle_booking_cancelled,
    handle_booking_confirmed,
    handle_booking_group_received,
    handle_booking_no_show,
    handle_booking_received,
    handle_booking_rescheduled,
)
from features.booking.views.public.commit import BookingCommitView
from features.main.models import Service


@pytest.fixture
def mock_appt():
    appt = MagicMock()
    appt.client.email = "test@example.com"
    appt.client.first_name = "Test"
    appt.service.name = "Test Service"
    appt.master.name = "Test Master"
    appt.datetime_start.strftime.return_value = "10.10.2026 10:00"
    appt.lang = "de"
    appt.get_cancel_reason_display.return_value = "Client Reason"
    return appt


def test_handle_booking_confirmed(mock_appt):
    spec = handle_booking_confirmed(mock_appt)
    assert spec.recipient_email == "test@example.com"
    assert spec.event_type == "booking.confirmed"
    assert spec.template_name == "emails/booking_confirmed.html"
    assert spec.context["service"] == "Test Service"


def test_handle_booking_cancelled(mock_appt):
    spec = handle_booking_cancelled(mock_appt)
    assert spec.recipient_email == "test@example.com"
    assert spec.event_type == "booking.cancelled"
    assert spec.template_name == "emails/booking_cancelled.html"
    assert spec.context["reason_text"] == "Client Reason"


def test_handle_booking_received(mock_appt):
    spec = handle_booking_received(mock_appt)
    assert spec.event_type == "booking.received"
    assert spec.subject_key == "bk_receipt_subject"
    assert spec.channels == ["email", "telegram"]


def test_handle_booking_group_received(client_obj, master, service):
    from features.booking.models import AppointmentGroup, AppointmentGroupItem

    service_two = Service.objects.create(
        category=service.category,
        name="Second Service",
        slug="second-service",
        price="30.00",
        duration=30,
        is_active=True,
    )
    group = AppointmentGroup.objects.create(client=client_obj, mode="same_day", source="website")
    appt_one = Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service,
        datetime_start=timezone.now() + timedelta(days=2),
        duration_minutes=service.duration,
        price=service.price,
    )
    appt_two = Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service_two,
        datetime_start=appt_one.datetime_start + timedelta(minutes=60),
        duration_minutes=service_two.duration,
        price=service_two.price,
    )
    AppointmentGroupItem.objects.create(group=group, appointment=appt_one, order=0)
    AppointmentGroupItem.objects.create(group=group, appointment=appt_two, order=1)

    spec = handle_booking_group_received(group)

    assert spec.recipient_email == "anna@test.local"
    assert spec.event_type == "booking.received"
    assert spec.template_name == "bk_group_booking"
    assert spec.channels == ["email", "telegram"]
    assert spec.context["total_price"] == "80.00"
    assert spec.context["datetime"] == appt_one.datetime_start.strftime("%d.%m.%Y %H:%M")
    assert "client_name" not in spec.context
    assert "language" not in spec.context
    assert spec.language == "de"
    assert [item["service_name"] for item in spec.context["items"]] == ["Test Service", "Second Service"]


def test_same_day_chain_sends_one_group_received_event(client_obj, master, service):
    service_two = Service.objects.create(
        category=service.category,
        name="Second Service",
        slug="second-service-chain",
        price="30.00",
        duration=30,
        is_active=True,
    )
    start = timezone.now() + timedelta(days=2)
    appt_one = Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service,
        datetime_start=start,
        duration_minutes=service.duration,
        price=service.price,
    )
    appt_two = Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service_two,
        datetime_start=start + timedelta(minutes=60),
        duration_minutes=service_two.duration,
        price=service_two.price,
    )
    cart = PublicCart(
        items=[
            PublicCartItem(
                service_id=service.id,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            ),
            PublicCartItem(
                service_id=service_two.id,
                service_title=service_two.name,
                duration=service_two.duration,
                price=service_two.price,
            ),
        ],
        date=start.date().isoformat(),
        time="10:00",
    )
    gateway = MagicMock()
    gateway.create_booking.return_value = [appt_one, appt_two]
    engine = MagicMock()

    with (
        patch("features.booking.views.public.commit.get_booking_engine_gateway", return_value=gateway),
        patch("features.conversations.services.notifications._get_engine", return_value=engine),
    ):
        redirect_url = BookingCommitView()._commit_same_day(MagicMock(), cart, client_obj)

    gateway.create_booking.assert_called_once_with(
        service_ids=[service.id, service_two.id],
        target_date=start.date(),
        selected_time="10:00",
        resource_id=None,
        client=client_obj,
        notify_received=False,
    )
    assert redirect_url == reverse("booking:success_group", kwargs={"token": appt_one.group_item.group.group_token})
    engine.dispatch_event.assert_has_calls([call("booking.group_received", appt_one.group_item.group)])
    assert engine.dispatch_event.call_count == 1


def test_handle_booking_no_show(mock_appt):
    spec = handle_booking_no_show(mock_appt)
    assert spec.event_type == "booking.no_show"
    assert spec.subject_key == "bk_noshow_subject"


def test_handle_booking_rescheduled(mock_appt):
    spec = handle_booking_rescheduled(mock_appt)
    assert spec.event_type == "booking.rescheduled"
    assert spec.subject_key == "bk_reschedule_subject"
