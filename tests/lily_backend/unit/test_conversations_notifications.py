from unittest.mock import MagicMock, patch

import pytest
from features.conversations.services.notifications import NotificationService


class TestConversationsNotifications:
    @pytest.fixture
    def mock_engine(self):
        with patch("features.conversations.services.notifications._get_engine") as mock:
            engine = MagicMock()
            mock.return_value = engine
            yield engine

    @pytest.fixture
    def mock_selector(self):
        # We need to mock _get_selector or at least _t used in the methods
        with patch("features.conversations.services.notifications._t", side_effect=lambda k, lang, f: f) as mock:
            yield mock

    @pytest.fixture
    def mock_should_notify(self):
        with patch("features.conversations.services.notifications._should_notify", return_value=True) as mock:
            yield mock

    def test_send_booking_receipt(self, mock_engine, mock_selector, mock_should_notify):
        recipient_email = "test@example.com"
        client_name = "Anna"
        context = {"time": "10:00"}

        NotificationService.send_booking_receipt(
            recipient_email=recipient_email, client_name=client_name, context=context, lang="de"
        )

        mock_engine.dispatch.assert_called_once()
        kwargs = mock_engine.dispatch.call_args.kwargs
        assert kwargs["recipient_email"] == recipient_email
        assert kwargs["template_name"] == "bk_receipt"
        assert kwargs["event_type"] == "booking.received"
        assert kwargs["time"] == "10:00"

    def test_send_booking_confirmation(self, mock_engine, mock_selector, mock_should_notify):
        NotificationService.send_booking_confirmation(
            recipient_email="test@example.com", client_name="Anna", context={"date": "2026-04-18"}
        )

        mock_engine.dispatch.assert_called_once()
        assert mock_engine.dispatch.call_args.kwargs["template_name"] == "bk_confirmation"
        assert mock_engine.dispatch.call_args.kwargs["event_type"] == "booking.confirmed"

    def test_send_booking_cancellation_with_reason(self, mock_engine, mock_selector, mock_should_notify):
        context = {"reason_text": "Sick leave"}
        NotificationService.send_booking_cancellation(
            recipient_email="test@example.com", client_name="Anna", context=context
        )

        mock_engine.dispatch.assert_called_once()
        # Verify reason was extracted into body
        body = mock_engine.dispatch.call_args.kwargs["email_body"]
        assert "Sick leave" in body
        assert "reason_text" not in mock_engine.dispatch.call_args.kwargs

    def test_send_account_verification(self, mock_engine, mock_selector):
        # account verification doesn't use _should_notify
        NotificationService.send_account_verification(
            recipient_email="verify@example.com", activate_url="http://link", user_name="User", signup=True
        )

        mock_engine.dispatch.assert_called_once()
        kwargs = mock_engine.dispatch.call_args.kwargs
        assert kwargs["template_name"] == "account/acc_verification"
        assert kwargs["event_type"] == "account.verification"
        assert kwargs["activate_url"] == "http://link"

    def test_send_password_reset(self, mock_engine, mock_selector):
        NotificationService.send_password_reset(
            recipient_email="reset@example.com", reset_url="http://reset", user_name="User"
        )

        mock_engine.dispatch.assert_called_once()
        assert mock_engine.dispatch.call_args.kwargs["password_reset_url"] == "http://reset"  # pragma: allowlist secret

    def test_should_notify_skip(self, mock_engine, mock_selector):
        with patch("features.conversations.services.notifications._should_notify", return_value=False):
            result = NotificationService.send_booking_receipt(
                recipient_email="optout@example.com", client_name="Anna", context={}
            )
            assert result is None
            mock_engine.dispatch.assert_not_called()
