import pytest
from unittest.mock import AsyncMock, MagicMock
from src.workers.notification_worker.tasks.campaign_tasks import send_campaign_batch_task
from src.workers.notification_worker.tasks.message_tasks import send_message_task

@pytest.mark.asyncio
async def test_send_campaign_batch_task_missing_payload():
    await send_campaign_batch_task({}, None)

@pytest.mark.asyncio
async def test_send_campaign_batch_task_no_pool():
    ctx = {"arq_pool": None, "redis": None}
    await send_campaign_batch_task(ctx, {"recipients": [1], "campaign_id": 1})

@pytest.mark.asyncio
async def test_send_campaign_batch_task_enqueue_failure():
    pool = AsyncMock()
    pool.enqueue_job.side_effect = Exception("Fail")
    ctx = {"arq_pool": pool}
    payload = {
        "campaign_id": 1,
        "recipients": [{"id": 1, "email": "a@b.com", "first_name": "A", "last_name": "B"}]
    }
    await send_campaign_batch_task(ctx, payload)
    pool.enqueue_job.assert_called_once()

@pytest.mark.asyncio
async def test_send_message_task_error(ctx_with_orchestrator):
    ctx_with_orchestrator["orchestrator"].send_message.side_effect = Exception("Fail")
    await send_message_task(ctx_with_orchestrator, "123", "msg", appointment_id=1)
    # Should catch and log

@pytest.fixture
def ctx_with_orchestrator():
    return {
        "orchestrator": MagicMock(send_message=AsyncMock()),
        "stream_manager": MagicMock(add_event=AsyncMock()),
    }
