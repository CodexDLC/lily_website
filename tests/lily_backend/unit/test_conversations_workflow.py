from unittest.mock import MagicMock, patch

import pytest
from features.conversations.models import Message
from features.conversations.services.workflow import (
    _update_message_state,
    apply_bulk_action,
    archive_thread,
    create_manual_message,
    create_reply,
    mark_thread_open,
    mark_thread_processed,
    mark_thread_read,
    mark_thread_spam,
    mark_thread_unread,
    trigger_manual_import,
)


@pytest.mark.django_db
class TestConversationsWorkflow:
    def test_create_manual_message_staff(self, django_user_model):
        user = django_user_model.objects.create(username="staff", first_name="Staff", last_name="User")
        # is_authenticated is a property, no need to set it

        with patch("features.conversations.services.workflow.notify_compose_new"):
            msg = create_manual_message(to_email="client@test.com", subject="Hi", body="Text", user=user)
        assert msg.sender_name == "Staff User"
        assert msg.sender_email == "client@test.com"
        assert msg.replies.count() == 1

    def test_create_manual_message_anonymous(self):
        user = MagicMock()
        user.is_authenticated = False
        with patch("features.conversations.services.workflow.notify_compose_new"):
            msg = create_manual_message(to_email="client@test.com", subject="Hi", body="Text", user=user)
        assert msg.sender_name == "client@test.com"
        assert msg.replies.first().sent_by is None

    def test_create_manual_message_dispatches_compose_new(self, django_user_model):
        user = django_user_model.objects.create(username="staff_dispatch", first_name="Staff", last_name="User")

        with patch("features.conversations.services.workflow.notify_compose_new") as mock_notify:
            msg = create_manual_message(
                to_email="client@test.com",
                subject="Hi there",
                body="Hello, this is a fresh outbound email.",
                user=user,
            )
            mock_notify.assert_called_once_with(msg, "client@test.com")

    def test_create_reply_success(self, django_user_model):
        msg = Message.objects.create(sender_name="1", sender_email="1@1.com")
        user = django_user_model.objects.create(username="reply_user")

        with patch("features.conversations.services.workflow.notify_thread_reply") as mock_notify:
            reply = create_reply(message=msg, body="Reply Text", user=user)
            assert reply.body == "Reply Text"
            assert msg.status == Message.Status.PROCESSED
            mock_notify.assert_called_once_with(msg, reply)

    def test_mark_thread_read(self):
        msg = Message.objects.create(is_read=False)
        mark_thread_read(message=msg)
        assert msg.is_read is True

    def test_mark_thread_unread(self):
        msg = Message.objects.create(is_read=True)
        mark_thread_unread(message=msg)
        assert msg.is_read is False

    def test_mark_thread_processed(self):
        msg = Message.objects.create(status=Message.Status.OPEN)
        mark_thread_processed(message=msg)
        assert msg.status == Message.Status.PROCESSED
        assert msg.is_read is True

    def test_mark_thread_open(self):
        msg = Message.objects.create(status=Message.Status.PROCESSED)
        mark_thread_open(message=msg)
        assert msg.status == Message.Status.OPEN

    def test_mark_thread_spam(self):
        msg = Message.objects.create(status=Message.Status.OPEN)
        mark_thread_spam(message=msg)
        assert msg.status == Message.Status.SPAM
        assert msg.is_read is True

    def test_archive_thread(self):
        msg = Message.objects.create(is_archived=False)
        archive_thread(message=msg)
        assert msg.is_archived is True
        assert msg.is_read is True

    def test_apply_bulk_action_dispatch(self):
        messages = [MagicMock(), MagicMock()]
        with patch("features.conversations.services.workflow.mark_thread_read") as mock_handler:
            count = apply_bulk_action(messages=messages, action="mark_read")
            assert count == 2
            assert mock_handler.call_count == 2

    def test_apply_bulk_action_unsupported(self):
        with pytest.raises(ValueError, match="Unsupported bulk action"):
            apply_bulk_action(messages=[], action="invalid_action")

    def test_trigger_manual_import_normalization_queued(self):
        with patch("features.conversations.services.workflow.trigger_email_import", return_value={"mode": "queued"}):
            result = trigger_manual_import()
            assert result["ok"] is True
            assert result["code"] == "email-import-queued"

    def test_trigger_manual_import_normalization_thread(self):
        with patch("features.conversations.services.workflow.trigger_email_import", return_value={"mode": "thread"}):
            result = trigger_manual_import()
            assert result["ok"] is True
            assert result["code"] == "email-import-thread"

    def test_update_message_state_selective(self):
        msg = Message.objects.create(status=Message.Status.OPEN, is_read=False, is_archived=False)
        # Update only status
        _update_message_state(message=msg, status=Message.Status.PROCESSED)
        assert msg.status == Message.Status.PROCESSED
        assert msg.is_read is False

        # Update multiple
        _update_message_state(message=msg, is_read=True, is_archived=True)
        assert msg.is_read is True
        assert msg.is_archived is True
