from unittest.mock import MagicMock, patch

import pytest
from features.conversations.services.workflow import apply_bulk_action, trigger_manual_import


class TestConversationsWorkflow:
    def test_apply_bulk_action_dispatch(self):
        messages = [MagicMock(), MagicMock()]

        # Test mark_read
        with patch("features.conversations.services.workflow.mark_thread_read") as mock_handler:
            count = apply_bulk_action(messages=messages, action="mark_read")
            assert count == 2
            assert mock_handler.call_count == 2
            mock_handler.assert_any_call(message=messages[0])
            mock_handler.assert_any_call(message=messages[1])

    def test_apply_bulk_action_unsupported(self):
        with pytest.raises(ValueError, match="Unsupported bulk action"):
            apply_bulk_action(messages=[], action="invalid_action")

    def test_trigger_manual_import_normalization_queued(self):
        with patch("features.conversations.services.workflow.trigger_email_import", return_value={"mode": "queued"}):
            result = trigger_manual_import()
            assert result["ok"] is True
            assert result["code"] == "email-import-queued"
            assert "queued" in result["message"]

    def test_trigger_manual_import_normalization_thread(self):
        with patch("features.conversations.services.workflow.trigger_email_import", return_value={"mode": "thread"}):
            result = trigger_manual_import()
            assert result["ok"] is True
            assert result["code"] == "email-import-thread"
            assert "started" in result["message"]
