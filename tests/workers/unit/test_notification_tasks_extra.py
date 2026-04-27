import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from arq import Retry
from src.workers.notification_worker.tasks.notification_tasks import (
    _report_campaign_status,
    send_universal_notification_task,
    send_rendered_notification_task,
)

@pytest.fixture
def mock_ctx():
    return {
        "notification_service": MagicMock(
            send_notification=AsyncMock(),
            send_rendered_notification=AsyncMock(),
            get_sms_text=MagicMock(return_value="SMS text"),
            get_absolute_logo_url=MagicMock(return_value="http://logo.png"),
        ),
        "internal_api": AsyncMock(),
        "arq_service": AsyncMock(),
        "job_try": 1,
    }

@pytest.mark.asyncio
async def test_report_campaign_status_success(mock_ctx):
    with patch("src.workers.core.config.WorkerSettings") as mock_settings:
        mock_settings.return_value.ops_worker_api_key = "test-token"  # pragma: allowlist secret
        await _report_campaign_status(mock_ctx, "campaign_123", "sent")
        mock_ctx["internal_api"].post.assert_called_once()

@pytest.mark.asyncio
async def test_report_campaign_status_no_api(mock_ctx):
    ctx = {"internal_api": None}
    await _report_campaign_status(ctx, "campaign_123", "sent")

@pytest.mark.asyncio
async def test_report_campaign_status_no_token(mock_ctx):
    with patch("src.workers.core.config.WorkerSettings") as mock_settings:
        mock_settings.return_value.ops_worker_api_key = None
        await _report_campaign_status(mock_ctx, "campaign_123", "sent")
        mock_ctx["internal_api"].post.assert_not_called()

@pytest.mark.asyncio
async def test_report_campaign_status_error(mock_ctx):
    with patch("src.workers.core.config.WorkerSettings") as mock_settings:
        mock_settings.return_value.ops_worker_api_key = "token"  # pragma: allowlist secret
        mock_ctx["internal_api"].post.side_effect = Exception("API error")
        # Should catch and log
        await _report_campaign_status(mock_ctx, "campaign_123", "sent")

@pytest.mark.asyncio
async def test_send_universal_rendered_success(mock_ctx):
    payload = {
        "notification_id": "nt_1",
        "recipient": {"email": "client@example.com", "first_name": "A"},
        "channels": ["email"],
        "mode": "rendered",
        "html_content": "<h1>Hello</h1>",
        "context_data": {},
    }
    await send_universal_notification_task(mock_ctx, payload=payload)
    mock_ctx["notification_service"].send_rendered_notification.assert_called_once()

@pytest.mark.asyncio
async def test_send_universal_campaign_failed_reporting(mock_ctx):
    payload = {
        "notification_id": "campaign_1",
        "recipient": {"email": "client@example.com", "first_name": "A"},
        "channels": ["email"],
        "template_name": "test",
        "context_data": {},
    }
    mock_ctx["notification_service"].send_notification.side_effect = Exception("Fail")
    mock_ctx["job_try"] = 5  # _CAMPAIGN_MAX_TRIES

    with patch("src.workers.core.config.WorkerSettings") as mock_settings:
        mock_settings.return_value.ops_worker_api_key = "token"  # pragma: allowlist secret
        await send_universal_notification_task(mock_ctx, payload=payload)
        # Should call _report_campaign_status with failed
        assert mock_ctx["internal_api"].post.called

@pytest.mark.asyncio
async def test_send_rendered_notification_task_success(mock_ctx):
    payload = {
        "email": "test@test.com",
        "html_content": "<html></html>",
        "subject": "Subj",
        "headers": {"X-Test": "1"}
    }
    await send_rendered_notification_task(mock_ctx, payload)
    mock_ctx["notification_service"].send_rendered_notification.assert_called_once()

@pytest.mark.asyncio
async def test_send_rendered_notification_task_missing_fields(mock_ctx):
    await send_rendered_notification_task(mock_ctx, {"email": "test@test.com"})
    mock_ctx["notification_service"].send_rendered_notification.assert_not_called()

@pytest.mark.asyncio
async def test_send_rendered_notification_task_failure(mock_ctx):
    mock_ctx["notification_service"].send_rendered_notification.side_effect = Exception("Fail")
    with pytest.raises(Retry):
        await send_rendered_notification_task(mock_ctx, {"email": "a@b.com", "html_content": "h"})
