from unittest.mock import AsyncMock, MagicMock
import pytest
from src.workers.notification_worker.tasks.campaign_tasks import send_campaign_batch_task

@pytest.fixture
def mock_ctx():
    return {
        "arq_pool": MagicMock(enqueue_job=AsyncMock()),
    }

@pytest.mark.asyncio
async def test_send_campaign_batch_task_success(mock_ctx):
    payload = {
        "campaign_id": 1,
        "subject": "Hello",
        "body_text": "Body",
        "arq_template_name": "mk_basic",
        "recipients": [
            {"id": 101, "email": "test@example.com", "first_name": "Anna", "last_name": "L", "unsubscribe_token": "token1"},
        ],
        "site_context": {"site_url": "http://site"},
    }

    await send_campaign_batch_task(mock_ctx, payload=payload)

    # Verify enqueue_job was called
    mock_ctx["arq_pool"].enqueue_job.assert_called_once()
    args, kwargs = mock_ctx["arq_pool"].enqueue_job.call_args
    assert args[0] == "send_universal_notification_task"

    task_payload = kwargs["payload"]
    assert task_payload["template_name"] == "mk_basic"
    assert task_payload["recipient"]["email"] == "test@example.com"
    assert task_payload["context_data"]["unsubscribe_url"] == "http://site/u/token1/"
    assert task_payload["context_data"]["body_text"] == "Body"

@pytest.mark.asyncio
async def test_send_campaign_batch_task_empty(mock_ctx):
    await send_campaign_batch_task(mock_ctx, payload={"recipients": []})
    mock_ctx["arq_pool"].enqueue_job.assert_not_called()
