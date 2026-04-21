from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.urls import reverse

from src.lily_backend.cabinet.views.client import ClientAppointmentsView, ClientHomeView, ClientSettingsView


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
