from unittest.mock import AsyncMock, MagicMock

import pytest

from src.workers.system_worker.tasks.booking import booking_maintenance_task


@pytest.fixture
def ctx():
    settings = MagicMock()
    settings.booking_worker_interval_sec = 60
    settings.booking_worker_stale_after_sec = 120

    registry = AsyncMock()
    registry.should_run.return_value = True

    return {"settings": settings, "heartbeat_registry": registry, "arq_service": AsyncMock(), "job_id": "test_job"}


@pytest.mark.asyncio
async def test_booking_maintenance_task_success(ctx):
    res = await booking_maintenance_task(ctx)
    assert res == {"status": "ok", "actions": 0}
    ctx["heartbeat_registry"].mark_started.assert_called_once()
    ctx["heartbeat_registry"].mark_finished.assert_called_once()
    # verify status was success
    args, kwargs = ctx["heartbeat_registry"].mark_finished.call_args
    assert kwargs["status"] == "success"


@pytest.mark.asyncio
async def test_booking_maintenance_task_skipped(ctx):
    ctx["heartbeat_registry"].should_run.return_value = False
    res = await booking_maintenance_task(ctx)
    assert res is None
    ctx["heartbeat_registry"].mark_finished.assert_called_once()
    args, kwargs = ctx["heartbeat_registry"].mark_finished.call_args
    assert kwargs["status"] == "skipped"


@pytest.mark.asyncio
async def test_booking_maintenance_task_failure(ctx):
    ctx["heartbeat_registry"].mark_started.side_effect = Exception("error_msg")
    with pytest.raises(Exception, match="error_msg"):
        await booking_maintenance_task(ctx)
    ctx["heartbeat_registry"].mark_finished.assert_called_once()
    args, kwargs = ctx["heartbeat_registry"].mark_finished.call_args
    assert kwargs["status"] == "failed"
