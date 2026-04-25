from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from src.lily_backend.cabinet.views.client import (
    ClientAppointmentsView,
    ClientCancelAppointmentView,
    ClientHomeView,
    ClientManageAppointmentView,
    ClientRescheduleConfirmView,
    ClientRescheduleSlotsView,
    ClientSettingsView,
)


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def client_user():
    user = MagicMock()
    user.is_active = True
    user.is_authenticated = True
    user.client_profile = MagicMock()
    user.profile = MagicMock()
    return user


@pytest.fixture
def mock_client_service():
    with patch("src.lily_backend.cabinet.views.client.ClientService") as mock:
        yield mock


def test_client_home_view(rf, client_user, mock_client_service):
    url = reverse("cabinet:client_home")
    request = rf.get(url)
    request.user = client_user

    mock_client_service.get_corner_context.return_value = {"summary": "test"}

    view = ClientHomeView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert request.cabinet_space == "client"
    mock_client_service.get_corner_context.assert_called_once_with(request)


def test_client_appointments_view(rf, client_user, mock_client_service):
    url = reverse("cabinet:client_appointments")
    request = rf.get(url)
    request.user = client_user

    mock_client_service.get_appointments_context.return_value = {"appointments": []}

    view = ClientAppointmentsView.as_view()
    response = view(request)

    assert response.status_code == 200
    mock_client_service.get_appointments_context.assert_called_once_with(request)


def test_client_settings_view_get(rf, client_user):
    url = reverse("cabinet:settings")
    request = rf.get(url)
    request.user = client_user

    view = ClientSettingsView.as_view()
    response = view(request)

    assert response.status_code == 200


@patch("src.lily_backend.cabinet.views.client.messages")
def test_client_settings_view_post_profile(mock_messages, rf, client_user):
    url = reverse("cabinet:settings")
    request = rf.post(
        url,
        data={
            "action": "profile",
            "first_name": "New",
            "last_name": "Name",
            "phone": "123",
            "email": "test@test.com",
            "instagram": "insta",
            "telegram": "tele",
            "birth_date": "1990-01-01",
        },
    )
    request.user = client_user

    view = ClientSettingsView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert client_user.client_profile.save.called
    assert client_user.profile.save.called
    assert client_user.client_profile.first_name == "New"


@patch("src.lily_backend.cabinet.views.client.messages")
def test_client_settings_view_post_notifications(mock_messages, rf, client_user):
    url = reverse("cabinet:settings")
    request = rf.post(url, data={"action": "notifications", "consent_marketing": "on", "notify_service": "on"})
    request.user = client_user

    view = ClientSettingsView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert client_user.client_profile.consent_marketing is True


@patch("src.lily_backend.cabinet.views.client.messages")
def test_client_settings_view_post_privacy(mock_messages, rf, client_user):
    url = reverse("cabinet:settings")
    request = rf.post(url, data={"action": "privacy", "show_avatar": "on", "consent_analytics": "on"})
    request.user = client_user

    view = ClientSettingsView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert client_user.profile.show_avatar is True
    assert client_user.client_profile.consent_analytics is True


@patch("src.lily_backend.cabinet.views.client.get_object_or_404")
def test_client_manage_appointment_context_flags_loyalty_warning(mock_get_object_or_404, rf):
    appointment = MagicMock()
    appointment.datetime_start = timezone.now() + timezone.timedelta(hours=2)
    appointment.can_cancel.return_value = True
    appointment.finalize_token = "token"
    mock_get_object_or_404.return_value = appointment
    request = rf.get("/cabinet/client/appointment/token/")
    request.user = MagicMock(is_authenticated=True)
    view = ClientManageAppointmentView()
    view.request = request
    view.kwargs = {"token": appointment.finalize_token}

    context = view.get_context_data()

    assert context["appointment"] is appointment
    assert context["can_cancel"] is True
    assert context["hours_until"] < 24
    assert context["show_loyalty_warning"] is True


@patch("src.lily_backend.cabinet.views.client.get_object_or_404")
def test_client_reschedule_slots_rejects_invalid_date(mock_get_object_or_404, rf, pending_appointment):
    request = rf.get("/cabinet/client/appointment/token/reschedule/slots/", data={"date": "bad-date"})
    request.user = MagicMock(is_authenticated=True)
    mock_get_object_or_404.return_value = pending_appointment

    response = ClientRescheduleSlotsView.as_view()(request, token=pending_appointment.finalize_token)

    assert response.status_code == 400


@patch("src.lily_backend.cabinet.views.client.render", return_value=HttpResponse("slots"))
@patch("features.booking.services.cabinet_availability.CabinetBookingAvailabilityService")
@patch("src.lily_backend.cabinet.views.client.get_object_or_404")
def test_client_reschedule_slots_renders_available_slots(
    mock_get_object_or_404,
    mock_availability_class,
    mock_render,
    rf,
    pending_appointment,
):
    request = rf.get("/cabinet/client/appointment/token/reschedule/slots/", data={"date": "2026-05-01"})
    request.user = MagicMock(is_authenticated=True)
    mock_get_object_or_404.return_value = pending_appointment
    mock_availability = mock_availability_class.return_value
    mock_availability.get_slots.return_value = [{"time": "10:00"}]

    response = ClientRescheduleSlotsView.as_view()(request, token=pending_appointment.finalize_token)

    assert response.status_code == 200
    mock_availability_class.assert_called_once_with(audience="public")
    mock_availability.get_slots.assert_called_once_with(
        booking_date="2026-05-01",
        service_ids=[pending_appointment.service_id],
    )
    assert mock_render.call_args.args[2]["slots"] == [{"time": "10:00"}]


@patch("src.lily_backend.cabinet.views.client.messages")
@patch("src.lily_backend.cabinet.views.client.get_object_or_404")
def test_client_reschedule_confirm_rejects_invalid_datetime(
    mock_get_object_or_404, mock_messages, rf, pending_appointment
):
    request = rf.post(
        "/cabinet/client/appointment/token/reschedule/confirm/",
        data={"date": "2026-05-01", "time": "bad-time"},
    )
    request.user = MagicMock(is_authenticated=True)
    mock_get_object_or_404.return_value = pending_appointment

    response = ClientRescheduleConfirmView.as_view()(request, token=pending_appointment.finalize_token)

    assert response.status_code == 302
    mock_messages.error.assert_called_once()


@patch("features.conversations.services.notifications._get_engine")
@patch("src.lily_backend.cabinet.views.client.messages")
@patch("src.lily_backend.cabinet.views.client.get_object_or_404")
def test_client_reschedule_confirm_updates_appointment(
    mock_get_object_or_404,
    mock_messages,
    mock_get_engine,
    rf,
    pending_appointment,
):
    request = rf.post(
        "/cabinet/client/appointment/token/reschedule/confirm/",
        data={"date": "2026-05-01", "time": "12:30"},
    )
    request.user = MagicMock(is_authenticated=True)
    mock_get_object_or_404.return_value = pending_appointment

    response = ClientRescheduleConfirmView.as_view()(request, token=pending_appointment.finalize_token)

    pending_appointment.refresh_from_db()
    local_start = timezone.localtime(pending_appointment.datetime_start)
    assert response.status_code == 302
    assert local_start.hour == 12
    assert local_start.minute == 30
    mock_get_engine.return_value.dispatch_event.assert_called_once_with("booking.rescheduled", pending_appointment)
    mock_messages.success.assert_called_once()


@patch("features.conversations.services.notifications._get_engine")
@patch("src.lily_backend.cabinet.views.client.messages")
@patch("src.lily_backend.cabinet.views.client.get_object_or_404")
def test_client_cancel_appointment_dispatches_notification(
    mock_get_object_or_404,
    mock_messages,
    mock_get_engine,
    rf,
    pending_appointment,
):
    request = rf.post("/cabinet/client/appointment/token/cancel/", data={"reason": "client"})
    request.user = MagicMock(is_authenticated=True)
    mock_get_object_or_404.return_value = pending_appointment

    response = ClientCancelAppointmentView.as_view()(request, token=pending_appointment.finalize_token)

    assert response.status_code == 302
    # It's called twice: once in appt.cancel() and once in the view
    assert mock_get_engine.return_value.dispatch_event.call_count == 2
    mock_get_engine.return_value.dispatch_event.assert_any_call("booking.cancelled", pending_appointment)
    mock_messages.success.assert_called_once()


@patch("src.lily_backend.cabinet.views.client.messages")
@patch("src.lily_backend.cabinet.views.client.get_object_or_404")
def test_client_cancel_appointment_reports_validation_error(mock_get_object_or_404, mock_messages, rf):
    appointment = MagicMock()
    appointment.cancel.side_effect = ValidationError("too late")
    request = rf.post("/cabinet/client/appointment/token/cancel/")
    request.user = MagicMock(is_authenticated=True)
    mock_get_object_or_404.return_value = appointment

    response = ClientCancelAppointmentView.as_view()(request, token="token")

    assert response.status_code == 302
    mock_messages.error.assert_called_once()
