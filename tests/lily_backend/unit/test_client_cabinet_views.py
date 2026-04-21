from unittest.mock import patch

import pytest
from cabinet.views.client import ClientAppointmentsView, ClientHomeView, ClientSettingsView
from tests.factories.system import ClientFactory, UserFactory, UserProfileFactory


@pytest.mark.django_db
class TestClientCabinetViews:
    def test_client_home_view_dispatch(self, rf):
        user = UserFactory()
        request = rf.get("/cabinet/")
        request.user = user
        view = ClientHomeView()
        view.request = request
        view.dispatch(request)
        assert request.cabinet_space == "client"
        assert request.cabinet_module == "client"

    def test_client_appointments_view_dispatch(self, rf):
        user = UserFactory()
        request = rf.get("/cabinet/appointments/")
        request.user = user
        view = ClientAppointmentsView()
        view.request = request
        view.dispatch(request)
        assert request.cabinet_space == "client"
        assert request.cabinet_module == "client"

    @patch("cabinet.views.client.messages")
    def test_client_settings_view_post_profile(self, mock_messages, rf):
        user = UserFactory()
        client = ClientFactory(user=user)
        profile = UserProfileFactory(user=user)
        request = rf.post(
            "/cabinet/settings/",
            {
                "action": "profile",
                "first_name": "NewFirst",
                "last_name": "NewLast",
                "phone": "+123456789",
                "email": "new@email.com",
                "instagram": "new_insta",
                "telegram": "new_tele",
                "birth_date": "1990-01-01",
            },
        )
        request.user = user
        view = ClientSettingsView()
        view.request = request
        view.post(request)
        client.refresh_from_db()
        profile.refresh_from_db()
        assert client.first_name == "NewFirst"
        assert client.phone == "+123456789"
        assert profile.instagram == "new_insta"
        assert profile.birth_date.isoformat() == "1990-01-01"
        mock_messages.success.assert_called()

    @patch("cabinet.views.client.messages")
    def test_client_settings_view_post_notifications(self, mock_messages, rf):
        user = UserFactory()
        client = ClientFactory(user=user)
        profile = UserProfileFactory(user=user)
        request = rf.post(
            "/cabinet/settings/",
            {"action": "notifications", "consent_marketing": "on", "notify_service": "on", "notify_reminders": ""},
        )
        request.user = user
        view = ClientSettingsView()
        view.request = request
        view.post(request)
        client.refresh_from_db()
        profile.refresh_from_db()
        assert client.consent_marketing is True
        assert profile.notify_service is True
        assert profile.notify_reminders is False
        mock_messages.success.assert_called()

    @patch("cabinet.views.client.messages")
    def test_client_settings_view_post_privacy(self, mock_messages, rf):
        user = UserFactory()
        client = ClientFactory(user=user)
        profile = UserProfileFactory(user=user)
        request = rf.post("/cabinet/settings/", {"action": "privacy", "show_avatar": "on", "consent_analytics": ""})
        request.user = user
        view = ClientSettingsView()
        view.request = request
        view.post(request)
        client.refresh_from_db()
        profile.refresh_from_db()
        assert profile.show_avatar is True
        assert client.consent_analytics is False
        mock_messages.success.assert_called()
