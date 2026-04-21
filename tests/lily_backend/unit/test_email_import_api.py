from unittest.mock import MagicMock, patch

import pytest
from features.conversations.api.import_email import AttachmentMetadata, InboundEmailPayload, import_email
from features.conversations.models import Message, MessageReply


@pytest.fixture
def email_payload():
    return InboundEmailPayload(
        sender_name="John Doe",
        sender_email="john@example.com",
        subject="Hello",
        body="Message body",
        message_id="msg-123",
    )


@pytest.mark.django_db
class TestEmailImportApi:
    @patch("system.api.auth.require_internal_scope")
    def test_import_email_creates_new_message(self, mock_auth, email_payload):
        request = MagicMock()

        result = import_email(request, email_payload)

        assert result["status"] == "message-created"
        message = Message.objects.get(pk=result["message_id"])
        assert message.sender_email == "john@example.com"
        assert message.body == "Message body"
        assert "Message-ID: msg-123" in message.admin_notes
        mock_auth.assert_called_once_with(request, "conversations.import")

    @patch("system.api.auth.require_internal_scope")
    def test_import_email_creates_reply_to_existing_thread(self, mock_auth, email_payload):
        # Create an existing message to reply to
        existing = Message.objects.create(
            sender_email="john@example.com", subject="Original", body="Original body", thread_key="thread-456"
        )

        email_payload.thread_key = "thread-456"
        request = MagicMock()

        result = import_email(request, email_payload)

        assert result["status"] == "reply-created"
        assert result["message_id"] == existing.pk
        reply = MessageReply.objects.get(pk=result["reply_id"])
        assert reply.message == existing
        assert reply.body == "Message body"

        existing.refresh_from_db()
        assert existing.status == Message.Status.OPEN
        assert existing.is_read is False

    @patch("system.api.auth.require_internal_scope")
    def test_import_email_with_attachments(self, mock_auth, email_payload):
        email_payload.attachments = [
            AttachmentMetadata(filename="test.pdf", size=1024),
            AttachmentMetadata(content_type="image/png"),
        ]
        request = MagicMock()

        result = import_email(request, email_payload)

        message = Message.objects.get(pk=result["message_id"])
        assert "Письмо содержало вложения: test.pdf (1024 bytes), image/png" in message.body

    @patch("system.api.auth.require_internal_scope")
    def test_import_email_spam_handling(self, mock_auth, email_payload):
        email_payload.spam = True
        request = MagicMock()

        result = import_email(request, email_payload)

        message = Message.objects.get(pk=result["message_id"])
        assert message.status == Message.Status.SPAM
        assert "Import status: spam" in message.admin_notes
