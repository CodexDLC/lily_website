from unittest.mock import AsyncMock, MagicMock

import pytest

from src.workers.system_worker.tasks.tracking import flush_tracking_task


@pytest.fixture
def ctx():
    settings = MagicMock()
    settings.tracking_flush_interval_sec = 60
    settings.tracking_flush_stale_after_sec = 120
    settings.tracking_worker_api_key = "secret_key"  # pragma: allowlist secret

    registry = AsyncMock()
    registry.should_run.return_value = True

    internal_api = AsyncMock()
    internal_api.post.return_value = {"flushed": 10}

    return {
        "settings": settings,
        "heartbeat_registry": registry,
        "internal_api": internal_api,
        "arq_service": AsyncMock(),
        "job_id": "test_job",
    }


@pytest.mark.asyncio
async def test_flush_tracking_task_success(ctx):
    res = await flush_tracking_task(ctx)
    assert res == {"flushed": 10}
    ctx["internal_api"].post.assert_called_once_with("/v1/tracking/flush", scope="tracking.flush", token="secret_key")
    ctx["heartbeat_registry"].mark_finished.assert_called_once()
    args, kwargs = ctx["heartbeat_registry"].mark_finished.call_args
    assert kwargs["status"] == "success"


@pytest.mark.asyncio
async def test_flush_tracking_task_skipped(ctx):
    ctx["heartbeat_registry"].should_run.return_value = False
    res = await flush_tracking_task(ctx)
    assert res is None
    ctx["heartbeat_registry"].mark_finished.assert_called_once()
    args, kwargs = ctx["heartbeat_registry"].mark_finished.call_args
    assert kwargs["status"] == "skipped"


@pytest.mark.asyncio
async def test_flush_tracking_task_failure(ctx):
    ctx["internal_api"].post.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        await flush_tracking_task(ctx)
    ctx["heartbeat_registry"].mark_finished.assert_called_once()
    args, kwargs = ctx["heartbeat_registry"].mark_finished.call_args
    assert kwargs["status"] == "failed"
