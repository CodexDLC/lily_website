from unittest.mock import MagicMock, patch

from features.conversations.services.alerts import (
    _build_compose_new_specs,
    _build_new_message_specs,
    _build_queue_adapter,
    _build_reply_context,
    _build_reply_subject,
    _build_subject,
    _build_text_content,
    _build_thread_reply_specs,
    _get_notification_engine,
    _StaticSubjectSelector,
    notify_compose_new,
    notify_new_message,
    notify_thread_reply,
)


class TestConversationsAlerts:
    def test_build_subject_logic(self):
        message = MagicMock()
        message.sender_name = "Anna"
        message.subject = "Hello"
        message.body = "Long body text here..."
        subject = _build_subject(message)
        assert "Anna" in subject
        assert "Hello" in subject

    def test_build_subject_from_body_preview(self):
        message = MagicMock()
        message.sender_name = "Anna"
        message.subject = None
        message.body = "This is a body that should be previewed"
        subject = _build_subject(message)
        assert "Anna" in subject
        assert "This is a body" in subject

    def test_build_text_content_logic(self):
        message = MagicMock()
        message.sender_name = "Anna"
        message.sender_email = "anna@example.com"
        message.body = "My message body"
        message.get_topic_display.return_value = "General"
        message.get_source_display.return_value = "Manual"
        message.get_channel_display.return_value = "Email"
        content = _build_text_content(message)
        assert "Anna <anna@example.com>" in content
        assert "General" in content
        assert "My message body" in content

    def test_build_reply_subject_existing(self):
        message = MagicMock()
        message.subject = "Original Subject"
        subject = _build_reply_subject(message)
        assert subject == "Re: Original Subject"

    def test_build_reply_subject_already_re(self):
        message = MagicMock()
        message.subject = "Re: Already Re"
        subject = _build_reply_subject(message)
        assert subject == "Re: Already Re"

    def test_build_reply_subject_empty(self):
        message = MagicMock()
        message.subject = "  "
        message.thread_key = "abcdef123456"  # pragma: allowlist secret
        subject = _build_reply_subject(message)
        assert "Re: Conversation abcdef12" in subject

    @patch("features.conversations.services.alerts._get_notification_engine")
    def test_notify_new_message_success(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_engine_factory.return_value = mock_engine
        msg = MagicMock(pk=1)
        notify_new_message(msg)
        mock_engine.dispatch_event.assert_called_once_with("conversations.new_message", msg)

    @patch("features.conversations.services.alerts._get_notification_engine")
    def test_notify_new_message_error(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_engine.dispatch_event.side_effect = Exception("error")
        mock_engine_factory.return_value = mock_engine
        # Should not raise
        notify_new_message(MagicMock(pk=1))

    @patch("features.conversations.services.alerts._get_notification_engine")
    def test_notify_thread_reply_success(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_engine_factory.return_value = mock_engine
        msg = MagicMock(pk=1)
        reply = MagicMock(pk=2)
        notify_thread_reply(msg, reply)
        mock_engine.dispatch_event.assert_called_once_with("conversations.thread_reply", msg, reply)

    @patch("features.conversations.services.alerts._get_notification_engine")
    def test_notify_thread_reply_error(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_engine.dispatch_event.side_effect = Exception("error")
        mock_engine_factory.return_value = mock_engine
        notify_thread_reply(MagicMock(pk=1), MagicMock(pk=2))

    @patch("features.conversations.services.alerts._get_notification_engine")
    def test_notify_compose_new_success(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_engine_factory.return_value = mock_engine
        msg = MagicMock(pk=7)
        notify_compose_new(msg, "client@example.com")
        mock_engine.dispatch_event.assert_called_once_with(
            "conversations.compose_new", msg, "client@example.com"
        )

    @patch("features.conversations.services.alerts._get_notification_engine")
    def test_notify_compose_new_error(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_engine.dispatch_event.side_effect = Exception("error")
        mock_engine_factory.return_value = mock_engine
        # Should not raise
        notify_compose_new(MagicMock(pk=7), "client@example.com")

    def test_build_compose_new_specs_uses_rendered_mode(self):
        msg = MagicMock(subject="Hello", body="Body text")
        spec = _build_compose_new_specs(msg, "client@example.com")
        assert spec.recipient_email == "client@example.com"
        assert spec.subject == "Hello"
        assert spec.event_type == "conversations.compose_new"
        assert spec.channels == ["email"]
        assert spec.mode == "rendered"
        assert spec.text_content == "Body text"
        assert spec.template_name == ""

    def test_build_compose_new_specs_blank_subject(self):
        msg = MagicMock(subject=None, body="Body only")
        spec = _build_compose_new_specs(msg, "client@example.com")
        assert spec.subject == ""
        assert spec.text_content == "Body only"

    def test_static_subject_selector(self):
        selector = _StaticSubjectSelector()
        assert selector.get("anything") is None

    def test_get_notification_engine_cached(self):
        _get_notification_engine.cache_clear()
        engine = _get_notification_engine()
        assert engine is _get_notification_engine()

    def test_build_queue_adapter_no_arq(self):
        with patch("features.conversations.services.alerts._HAS_ARQ", False):
            from codex_django.notifications import DjangoDirectAdapter

            adapter = _build_queue_adapter()
            assert isinstance(adapter, DjangoDirectAdapter)

    def test_build_queue_adapter_with_arq(self):
        # We need to mock settings and the import
        with patch("features.conversations.services.alerts._HAS_ARQ", True):
            mock_client = MagicMock()
            with patch("core.arq.client.DjangoArqClient", mock_client, create=True):
                from codex_django.notifications import DjangoQueueAdapter

                adapter = _build_queue_adapter()
                assert isinstance(adapter, DjangoQueueAdapter)

    @patch("features.conversations.services.alerts._iter_admin_specs")
    def test_build_new_message_specs(self, mock_iter):
        mock_iter.return_value = ["spec"]
        assert _build_new_message_specs(MagicMock()) == ["spec"]

    @patch("features.conversations.services.alerts._build_reply_subject")
    @patch("features.conversations.services.alerts._build_reply_context")
    def test_build_thread_reply_specs(self, mock_ctx, mock_subj):
        msg = MagicMock(sender_email="test@test.com")
        reply = MagicMock(body="Hello")
        mock_ctx.return_value = {"reply_text": "Hello"}
        mock_subj.return_value = "Subject"

        spec = _build_thread_reply_specs(msg, reply)
        assert spec.recipient_email == "test@test.com"
        assert spec.context["reply_text"] == "Hello"

    def test_build_reply_context(self):
        msg = MagicMock(pk=1, thread_key="tk")
        reply = MagicMock(pk=2)
        with patch("features.conversations.services.alerts.build_mailbox_correlation_data", create=True) as mock_corr:
            mock_corr.return_value = MagicMock(thread_key="tk", reply_match_token="rm")
            ctx = _build_reply_context(msg, reply)
            assert ctx["message_id"] == 1
            assert ctx["thread_key"] == "tk"

    def test_iter_admin_specs(self):
        from features.conversations.services.alerts import _iter_admin_specs

        with patch("django.conf.settings.ADMINS", [(1, "admin@test.com"), (2, None)]):
            msg = MagicMock()
            specs = list(_iter_admin_specs(msg))
            assert len(specs) == 1
            assert specs[0].recipient_email == "admin@test.com"
