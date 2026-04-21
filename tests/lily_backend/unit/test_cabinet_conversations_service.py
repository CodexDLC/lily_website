from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpRequest
from features.conversations.models import Message

from src.lily_backend.cabinet.services.conversations import ConversationsService, _build_thread_actions


@pytest.mark.django_db
class TestConversationsService:
    @patch("src.lily_backend.cabinet.services.conversations.get_paginated_messages")
    @patch("src.lily_backend.cabinet.services.conversations.get_topic_counts")
    @patch("src.lily_backend.cabinet.services.conversations.get_status_counts")
    @patch("src.lily_backend.cabinet.services.conversations.get_unread_count")
    def test_get_inbox_context(self, mock_unread, mock_status, mock_topics, mock_paginated):
        mock_paginated.return_value = ["msg1"]
        mock_topics.return_value = {"topic1": 1}
        mock_status.return_value = {"open": 1}
        mock_unread.return_value = 5

        req = HttpRequest()
        req.GET = {"folder": "open", "topic": "t1", "page": "1"}

        ctx = ConversationsService.get_inbox_context(req)
        assert ctx["messages"] == ["msg1"]
        assert ctx["unread_messages_count"] == 5
        assert ctx["active_folder"] == "open"
        assert ctx["active_topic"] == "t1"

    @patch("src.lily_backend.cabinet.services.conversations.get_paginated_messages")
    def test_get_inbox_context_email_import(self, mock_paginated):
        req = HttpRequest()
        req.GET = {"folder": "email_import"}
        ConversationsService.get_inbox_context(req)
        # Check source=EMAIL_IMPORT was passed
        mock_paginated.assert_called_once()
        args, kwargs = mock_paginated.call_args
        assert kwargs["source"] == Message.Source.EMAIL_IMPORT
        assert kwargs["status"] == "all"

    @patch("src.lily_backend.cabinet.services.conversations.get_message")
    @patch("src.lily_backend.cabinet.services.conversations.get_replies")
    def test_get_thread_context(self, mock_replies, mock_get_msg):
        msg = MagicMock(pk=1, status="open", is_read=False)
        mock_get_msg.return_value = msg
        mock_replies.return_value = ["reply1"]

        ctx = ConversationsService.get_thread_context(pk=1)
        assert ctx["message"] == msg
        assert ctx["replies"] == ["reply1"]
        assert len(ctx["thread_actions"]) > 0

    @patch("src.lily_backend.cabinet.services.conversations.get_message_or_404")
    @patch("src.lily_backend.cabinet.services.conversations.create_reply")
    def test_reply_to_thread_success(self, mock_create, mock_get_msg):
        msg = MagicMock(pk=1)
        mock_get_msg.return_value = msg
        user = MagicMock()

        res = ConversationsService.reply_to_thread(pk=1, body="Hello", user=user)
        assert res["ok"] is True
        assert res["code"] == "reply-created"
        mock_create.assert_called_once_with(message=msg, body="Hello", user=user)

    def test_reply_to_thread_empty(self):
        with patch("src.lily_backend.cabinet.services.conversations.get_message_or_404") as mock_get:
            mock_get.return_value = MagicMock(pk=1)
            res = ConversationsService.reply_to_thread(pk=1, body="", user=None)
            assert res["code"] == "reply-empty"

    @patch("src.lily_backend.cabinet.services.conversations.get_message_or_404")
    def test_perform_thread_action_success(self, mock_get_msg):
        msg = MagicMock(pk=1)
        mock_get_msg.return_value = msg

        actions = {
            "mark_read": "mark_thread_read",
            "mark_unread": "mark_thread_unread",
            "mark_processed": "mark_thread_processed",
            "mark_open": "mark_thread_open",
            "mark_spam": "mark_thread_spam",
            "archive": "archive_thread",
        }
        for action, patch_name in actions.items():
            with patch(f"src.lily_backend.cabinet.services.conversations.{patch_name}") as mock_handler:
                res = ConversationsService.perform_thread_action(pk=1, action=action)
                assert res["ok"] is True
                mock_handler.assert_called_once()
                if action in {"archive", "mark_spam"}:
                    assert "conversations" in res["redirect_url"]
                    assert "1" not in res["redirect_url"]  # Should redirect to inbox
                else:
                    assert str(msg.pk) in res["redirect_url"]

    def test_perform_thread_action_invalid(self):
        with patch("src.lily_backend.cabinet.services.conversations.get_message_or_404") as mock_get:
            mock_get.return_value = MagicMock(pk=1)
            res = ConversationsService.perform_thread_action(pk=1, action="invalid")
            assert res["ok"] is False
            assert res["code"] == "thread-action-invalid"

    @patch("src.lily_backend.cabinet.services.conversations.create_manual_message")
    def test_compose_message_success(self, mock_create):
        mock_create.return_value = MagicMock(pk=10)
        req = HttpRequest()
        req.POST = {"to_email": "test@test.com", "subject": "Hi", "body": "Body"}
        req.user = MagicMock()

        res = ConversationsService.compose_message(request=req)
        assert res["ok"] is True
        assert res["code"] == "compose-created"
        mock_create.assert_called_once()

    def test_compose_message_invalid(self):
        req = HttpRequest()
        req.POST = {"to_email": "", "body": ""}
        res = ConversationsService.compose_message(request=req)
        assert res["ok"] is False

    @patch("src.lily_backend.cabinet.services.conversations.apply_bulk_action")
    @patch("src.lily_backend.cabinet.services.conversations.get_message_queryset")
    def test_perform_bulk_action_success(self, mock_qs_factory, mock_apply):
        mock_qs = MagicMock()
        mock_qs_factory.return_value = mock_qs
        mock_qs.filter.return_value = [MagicMock(pk=1), MagicMock(pk=2)]
        mock_apply.return_value = 2

        req = HttpRequest()
        req.POST = MagicMock()
        req.POST.get.return_value = "archive"
        req.POST.getlist.return_value = ["1", "2"]

        res = ConversationsService.perform_bulk_action(request=req)
        assert res["ok"] is True
        assert res["meta"]["updated_count"] == 2
        mock_apply.assert_called_once()

    def test_perform_bulk_action_missing_action(self):
        req = HttpRequest()
        req.POST = MagicMock()
        req.POST.get.return_value = ""
        res = ConversationsService.perform_bulk_action(request=req)
        assert res["ok"] is False

    def test_perform_bulk_action_empty_selection(self):
        req = HttpRequest()
        req.POST = MagicMock()
        req.POST.get.return_value = "archive"
        req.POST.getlist.return_value = []
        res = ConversationsService.perform_bulk_action(request=req)
        assert res["ok"] is False

    def test_perform_bulk_action_invalid_action(self):
        req = HttpRequest()
        req.POST = MagicMock()
        req.POST.get.return_value = "invalid"
        req.POST.getlist.return_value = ["1"]
        res = ConversationsService.perform_bulk_action(request=req)
        assert res["ok"] is False

    @patch("src.lily_backend.cabinet.services.conversations.trigger_manual_import")
    def test_check_inbox(self, mock_trigger):
        mock_trigger.return_value = {"ok": True}
        res = ConversationsService.check_inbox()
        assert res["ok"] is True
        assert "redirect_url" in res

    def test_build_thread_actions_none(self):
        assert _build_thread_actions(None) == []

    def test_build_thread_actions_processed(self):
        msg = MagicMock(status="processed", is_read=True)
        actions = _build_thread_actions(msg)
        assert not any(a["slug"] == "mark_processed" for a in actions)
        assert any(a["slug"] == "mark_unread" for a in actions)
