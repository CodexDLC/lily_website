from unittest.mock import MagicMock, patch

import pytest
from system.services.auth import AuthService


class TestSystemAuth:
    @pytest.fixture
    def mock_redis_mgr(self):
        with patch("system.services.auth.ActionTokenRedisManager") as mock:
            instance = mock.return_value
            yield instance

    def test_generate_reschedule_link(self, mock_redis_mgr):
        appointment = MagicMock()
        appointment.id = 123

        mock_redis_mgr.create_token.return_value = "secret-token"

        service = AuthService()
        link = service.generate_reschedule_link(appointment, "2026-04-18T10:00:00")

        assert "secret-token" in link
        mock_redis_mgr.create_token.assert_called_once_with(
            appointment_id=123, proposed_slot="2026-04-18T10:00:00", action_type="reschedule", ttl_hours=24
        )

    def test_verify_action_token(self, mock_redis_mgr):
        mock_redis_mgr.get_token_data.return_value = {"id": 123}

        service = AuthService()
        data = service.verify_action_token("valid-token")

        assert data == {"id": 123}
        mock_redis_mgr.get_token_data.assert_called_once_with("valid-token")

    def test_consume_token(self, mock_redis_mgr):
        service = AuthService()
        service.consume_token("used-token")

        mock_redis_mgr.delete_token.assert_called_once_with("used-token")
