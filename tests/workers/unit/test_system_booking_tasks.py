from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from src.workers.system_worker.tasks.booking import TASK_ID, _schedule_next, booking_maintenance_task


@pytest.fixture
def mock_ctx():
    return {
        "settings": MagicMock(booking_worker_interval_sec=60, booking_worker_stale_after_sec=120),
        "heartbeat_registry": AsyncMock(),
        "arq_service": AsyncMock(),
        "job_id": "test-job-123",
    }


@pytest.mark.asyncio
class TestBookingMaintenanceTask:
    async def test_run_success(self, mock_ctx):
        # Setup registry to allow run
        mock_ctx["heartbeat_registry"].should_run.return_value = True

        res = await booking_maintenance_task(mock_ctx)

        assert res == {"status": "ok", "actions": 0}
        mock_ctx["heartbeat_registry"].mark_started.assert_called_once()
        mock_ctx["heartbeat_registry"].mark_finished.assert_called_with(ANY, status="success")
        mock_ctx["heartbeat_registry"].release_lock.assert_called_once_with(TASK_ID)

        # Verify next job enqueued
        mock_ctx["arq_service"].enqueue_job.assert_called_once()

    async def test_run_skipped(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = False

        res = await booking_maintenance_task(mock_ctx)

        assert res is None
        mock_ctx["heartbeat_registry"].mark_finished.assert_called_with(ANY, status="skipped")
        # release_lock SHOULD NOT be called because task returns before acquiring lock
        mock_ctx["heartbeat_registry"].release_lock.assert_not_called()

    async def test_run_error(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = True
        mock_ctx["heartbeat_registry"].mark_started.side_effect = Exception("Registry error")

        with pytest.raises(Exception, match="Registry error"):
            await booking_maintenance_task(mock_ctx)

        mock_ctx["heartbeat_registry"].mark_finished.assert_called_with(ANY, status="failed", error="Registry error")
        mock_ctx["heartbeat_registry"].release_lock.assert_called_once_with(TASK_ID)

    async def test_schedule_next_no_arq(self, mock_ctx):
        del mock_ctx["arq_service"]
        task = MagicMock(expected_interval_sec=60, queue_name="system", task_id="test")

        await _schedule_next(mock_ctx, task)
        # Should finish silently without error
