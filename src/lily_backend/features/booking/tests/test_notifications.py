from unittest.mock import MagicMock

import pytest

from features.booking.services.notifications import (
    handle_booking_cancelled,
    handle_booking_confirmed,
    handle_booking_no_show,
    handle_booking_received,
    handle_booking_rescheduled,
)


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


def test_handle_booking_no_show(mock_appt):
    spec = handle_booking_no_show(mock_appt)
    assert spec.event_type == "booking.no_show"
    assert spec.subject_key == "bk_noshow_subject"


def test_handle_booking_rescheduled(mock_appt):
    spec = handle_booking_rescheduled(mock_appt)
    assert spec.event_type == "booking.rescheduled"
    assert spec.subject_key == "bk_reschedule_subject"
