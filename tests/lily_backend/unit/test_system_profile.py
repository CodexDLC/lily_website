from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from system.services.client_profile import ClientProfileService


class TestSystemProfile:
    @pytest.fixture
    def mock_selector(self):
        with patch("system.services.client_profile.ClientProfileSelector") as mock:
            yield mock

    def test_get_profile_payload(self, mock_selector):
        user = MagicMock()
        user.first_name = "UserFirst"
        user.last_name = "UserLast"
        user.email = "user@example.com"

        profile = MagicMock()
        profile.first_name = "ProfileFirst"
        profile.last_name = ""  # Should fallback to user
        profile.patronymic = "Patro"
        profile.phone = "123"
        profile.birth_date = date(1990, 1, 1)

        mock_selector.get_or_create_profile.return_value = profile

        pref_profile, payload = ClientProfileService.get_profile_payload(user)

        assert payload.first_name == "ProfileFirst"
        assert payload.last_name == "UserLast"  # Fallback
        assert payload.patronymic == "Patro"
        assert payload.birth_date == "1990-01-01"

    def test_save_profile_success(self, mock_selector):
        user = MagicMock(spec=["first_name", "last_name", "email", "save"])
        profile = MagicMock()
        mock_selector.get_or_create_profile.return_value = profile

        form_data = {
            "first_name": " NewName ",
            "last_name": "NewLast",
            "email": "new@ex.com",
            "birth_date": "1995-05-05",
        }

        ok, msg = ClientProfileService.save_profile(user, form_data)

        assert ok is True
        assert user.first_name == "NewName"
        assert profile.first_name == "NewName"
        assert profile.birth_date == date(1995, 5, 5)
        user.save.assert_called_once()
        profile.save.assert_called_once()

    def test_save_profile_invalid_date(self, mock_selector):
        user = MagicMock()
        profile = MagicMock()
        mock_selector.get_or_create_profile.return_value = profile

        form_data = {"birth_date": "invalid-date"}

        ok, msg = ClientProfileService.save_profile(user, form_data)

        assert ok is False
        assert "format" in msg.lower()

    def test_save_profile_empty_date(self, mock_selector):
        user = MagicMock()
        profile = MagicMock()
        mock_selector.get_or_create_profile.return_value = profile

        form_data = {"birth_date": ""}

        ok, msg = ClientProfileService.save_profile(user, form_data)

        assert ok is True
        assert profile.birth_date is None
