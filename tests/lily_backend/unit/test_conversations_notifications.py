from unittest.mock import MagicMock, patch

import pytest
from features.conversations.services.notifications import (
    NotificationService,
    _handle_new_contact_message,
)


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

    def test_get_selector(self):
        from features.conversations.services.notifications import _get_selector

        selector = _get_selector()
        assert selector is not None

    def test_get_engine(self):
        from features.conversations.services.notifications import _get_engine

        engine = _get_engine()
        assert engine is not None

    def test_get_engine_no_arq(self):
        with patch("features.conversations.services.notifications._HAS_ARQ", False):
            from features.conversations.services.notifications import _get_engine

            # Reset cache if it was used
            _get_engine.cache_clear()
            engine = _get_engine()
            assert engine is not None

    def test_t_fallback(self):
        from features.conversations.services.notifications import _t

        with patch("features.conversations.services.notifications._get_selector") as mock:
            mock.return_value.get.return_value = None
            assert _t("key", "de", "fallback") == "fallback"

    def test_should_notify_logic(self):
        from features.conversations.services.notifications import _should_notify

        mock_user = MagicMock()
        mock_user.profile.notify_service = False
        with patch("django.contrib.auth.get_user_model") as mock_get_user:
            mock_get_user.return_value.objects.filter.return_value.first.return_value = mock_user
            assert _should_notify("test@test.com", "notify_service") is False

    def test_should_notify_no_user(self):
        from features.conversations.services.notifications import _should_notify

        with patch("django.contrib.auth.get_user_model") as mock_get_user:
            mock_get_user.return_value.objects.filter.return_value.first.return_value = None
            assert _should_notify("unknown@test.com", "any") is True

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

    def test_api_methods_skipped_if_not_notifying(self):
        # We need to mock _should_notify to return False
        # Patch it in the module where it's used
        with (
            patch("features.conversations.services.notifications._should_notify", return_value=False),
            patch("features.conversations.services.notifications._get_engine") as mock_engine,
        ):
            NotificationService.send_booking_receipt(recipient_email="test@test.com", client_name="Anna", context={})
            # Since it returns early, _get_engine().dispatch shouldn't be called
            mock_engine.return_value.dispatch.assert_not_called()

    def test_handle_new_contact_message_no_admin_email(self):
        mock_msg = MagicMock()
        mock_msg.sender_name = "John"
        mock_msg.sender_email = "john@test.com"
        mock_msg.body = "Hello"
        mock_msg.subject = None

        # Test the 'continue' if email is empty in ADMINS
        with patch("django.conf.settings.ADMINS", [("Admin", "")]):
            specs = _handle_new_contact_message(mock_msg)
            assert len(specs) == 0

    def test_send_booking_reschedule(self, mock_engine, mock_selector, mock_should_notify):
        NotificationService.send_booking_reschedule(recipient_email="test@example.com", client_name="Anna", context={})
        assert mock_engine.dispatch.call_args.kwargs["template_name"] == "bk_reschedule"

    def test_send_booking_reminder(self, mock_engine, mock_selector):
        with patch("features.conversations.services.notifications._should_notify", return_value=True):
            NotificationService.send_booking_reminder(
                recipient_email="test@example.com", client_name="Anna", context={}
            )
            assert mock_engine.dispatch.call_args.kwargs["template_name"] == "bk_reminder"

    def test_send_booking_no_show(self, mock_engine, mock_selector, mock_should_notify):
        NotificationService.send_booking_no_show(recipient_email="test@example.com", client_name="Anna", context={})
        assert mock_engine.dispatch.call_args.kwargs["template_name"] == "bk_no_show"

    def test_send_contact_receipt(self, mock_engine, mock_selector):
        NotificationService.send_contact_receipt(
            recipient_email="customer@test.com", client_name="Bob", message_text="Hi", request_id=123
        )
        assert mock_engine.dispatch.call_args.kwargs["template_name"] == "ct_receipt"
        assert mock_engine.dispatch.call_args.kwargs["request_id"] == 123

    def test_send_account_already_exists(self, mock_engine, mock_selector):
        NotificationService.send_account_already_exists(
            recipient_email="exists@test.com",
            password_reset_url="http://reset",  # pragma: allowlist secret
        )
        assert mock_engine.dispatch.call_args.kwargs["template_name"] == "account/acc_already_exists"

    def test_send_admin_reply(self, mock_engine, mock_selector):
        NotificationService.send_admin_reply(
            recipient_email="client@test.com", reply_text="Hello", history_text="...", request_id=456
        )
        assert mock_engine.dispatch.call_args.kwargs["template_name"] == "ct_reply"

    def test_handle_new_contact_message(self):
        from features.conversations.services.notifications import _handle_new_contact_message

        mock_msg = MagicMock()
        mock_msg.sender_name = "John"
        mock_msg.sender_email = "john@example.com"
        mock_msg.subject = "Support"
        mock_msg.body = "Help me"
        mock_msg.get_topic_display.return_value = "Support"
        mock_msg.get_source_display.return_value = "Web"

        with patch("django.conf.settings.ADMINS", [("Admin", "admin@lily.com")]):
            specs = _handle_new_contact_message(mock_msg)
            assert specs[0].recipient_email == "admin@lily.com"
            assert "John" in specs[0].text_content

    def test_account_verification_fallbacks(self):
        from features.conversations.services.notifications import _account_verification_fallbacks

        subj, body, greet = _account_verification_fallbacks("de", True)
        assert "bestätigen" in subj

        subj, body, greet = _account_verification_fallbacks("ru", False)
        assert "Подтвердите" in subj

        subj, body, greet = _account_verification_fallbacks("unknown", True)
        assert "verify" in subj

    def test_handle_new_contact_message_missing_email(self):
        from features.conversations.services.notifications import _handle_new_contact_message

        mock_msg = MagicMock()
        mock_msg.sender_name = "John"
        mock_msg.sender_email = None
        mock_msg.body = "Hello"
        mock_msg.subject = None
        mock_msg.get_topic_display.return_value = "Support"
        mock_msg.get_source_display.return_value = "Web"

        with patch("django.conf.settings.ADMINS", [("Admin", "admin@lily.com")]):
            specs = _handle_new_contact_message(mock_msg)
            assert len(specs) == 1
            assert "<None>" in specs[0].text_content
