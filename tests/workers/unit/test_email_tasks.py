import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.workers.notification_worker.tasks.email_tasks import send_email_task, _mailbox_headers

@pytest.mark.asyncio
async def test_send_email_task_success():
    ctx = {
        "notification_service": MagicMock(),
        "orchestrator": AsyncMock(),
    }
    ctx["notification_service"].enrich_email_context.return_value = {"full": "ctx"}
    ctx["notification_service"].renderer.render.return_value = "<html>Content</html>"
    ctx["orchestrator"].send_email.return_value = True
    
    with patch("src.workers.notification_worker.tasks.email_tasks._send_status_update", new_callable=AsyncMock) as mock_status:
        await send_email_task(ctx, "test@test.com", "Sub", "tpl", {"thread_key": "tk_1"}, appointment_id=123)
        
        mock_status.assert_called_with(ctx, 123, "email", "success", template_name="tpl")
        ctx["orchestrator"].send_email.assert_called_once()
        # Check if headers were passed
        args, kwargs = ctx["orchestrator"].send_email.call_args
        assert kwargs["headers"]["X-Lily-Thread-Key"] == "tk_1"

@pytest.mark.asyncio
async def test_send_email_task_missing_services():
    ctx = {}
    with patch("src.workers.notification_worker.tasks.email_tasks._send_status_update", new_callable=AsyncMock) as mock_status:
        await send_email_task(ctx, "test@test.com", "Sub", "tpl", {}, appointment_id=123)
        mock_status.assert_called_with(ctx, 123, "email", "failed", template_name="tpl")

@pytest.mark.asyncio
async def test_send_email_task_failure():
    ctx = {
        "notification_service": MagicMock(),
        "orchestrator": AsyncMock(),
    }
    ctx["orchestrator"].send_email.return_value = False
    
    with patch("src.workers.notification_worker.tasks.email_tasks._send_status_update", new_callable=AsyncMock) as mock_status:
        await send_email_task(ctx, "test@test.com", "Sub", "tpl", {})
        mock_status.assert_called_with(ctx, None, "email", "failed", template_name="tpl")

@pytest.mark.asyncio
async def test_send_email_task_exception():
    ctx = {
        "notification_service": MagicMock(),
        "orchestrator": AsyncMock(),
    }
    ctx["orchestrator"].send_email.side_effect = Exception("Boom")
    
    with (
        patch("src.workers.notification_worker.tasks.email_tasks._send_status_update", new_callable=AsyncMock) as mock_status,
        pytest.raises(Exception, match="Boom")
    ):
        await send_email_task(ctx, "test@test.com", "Sub", "tpl", {})
        
    mock_status.assert_called_with(ctx, None, "email", "failed", template_name="tpl")

def test_mailbox_headers_none():
    assert _mailbox_headers({}) is None

def test_mailbox_headers_reply_match_token():
    headers = _mailbox_headers({"reply_match_token": "token123"})
    assert headers["X-Lily-Thread-Key"] == "token123"
    assert headers["Message-ID"] == "<token123>"
