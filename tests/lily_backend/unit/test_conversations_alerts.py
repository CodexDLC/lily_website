from unittest.mock import MagicMock

from features.conversations.services.alerts import _build_reply_subject, _build_subject, _build_text_content


class TestConversationsAlerts:
    def test_build_subject_logic(self):
        message = MagicMock()
        message.sender_name = "Anna"
        message.subject = "Hello"
        message.body = "Long body text here..."

        # [New message] Anna - Hello
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
        assert subject == "Re: Already Re"  # Should not double Re:

    def test_build_reply_subject_empty(self):
        message = MagicMock()
        message.subject = "  "
        message.thread_key = "abcdef123456"  # pragma: allowlist secret

        # Re: Conversation abcdef12
        subject = _build_reply_subject(message)
        assert "Re: Conversation abcdef12" in subject
