from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from src.workers.system_worker.tasks.booking import TASK_ID, _schedule_next, booking_maintenance_task


@pytest.fixture
def mock_ctx():
    internal_api = AsyncMock()
    internal_api.get.return_value = []

    return {
        "settings": MagicMock(
            booking_worker_interval_sec=60,
            booking_worker_stale_after_sec=120,
            booking_worker_api_key="test-token",  # pragma: allowlist secret
        ),
        "heartbeat_registry": AsyncMock(),
        "arq_service": AsyncMock(),
        "internal_api": internal_api,
        "job_id": "test-job-123",
    }


@pytest.mark.asyncio
class TestBookingMaintenanceTask:
    async def test_run_success(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = True

        res = await booking_maintenance_task(mock_ctx)

        assert res == {"status": "ok", "actions": 0}
        mock_ctx["heartbeat_registry"].mark_started.assert_called_once()
        mock_ctx["heartbeat_registry"].mark_finished.assert_called_with(ANY, status="success")
        mock_ctx["heartbeat_registry"].release_lock.assert_called_once_with(TASK_ID)
        mock_ctx["arq_service"].enqueue_job.assert_called_once()

    async def test_run_skipped(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = False

        res = await booking_maintenance_task(mock_ctx)

        assert res is None
        mock_ctx["heartbeat_registry"].mark_finished.assert_called_with(ANY, status="skipped")
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

    async def test_reminders_branch_no_api_key(self, mock_ctx):
        mock_ctx["settings"].booking_worker_api_key = None
        mock_ctx["heartbeat_registry"].should_run.return_value = True

        res = await booking_maintenance_task(mock_ctx)

        assert res == {"status": "ok", "actions": 0}
        mock_ctx["internal_api"].get.assert_not_called()

    async def test_reminders_branch_queues_tasks(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = True
        mock_ctx["internal_api"].get.return_value = [
            {
                "id": 42,
                "client_email": "client@example.com",
                "name": "Anna",
                "service_name": "Haircut",
                "datetime": "27.04.2026 14:00",
                "lang": "de",
                "master_name": "Maria",
            }
        ]
        mock_ctx["arq_service"].enqueue_job.return_value = AsyncMock()

        res = await booking_maintenance_task(mock_ctx)

        assert res == {"status": "ok", "actions": 1}
        mock_ctx["internal_api"].post.assert_called_once_with(
            "/booking/appointments/42/mark-reminder-sent",
            scope="booking.worker",
            token="test-token",
        )

    async def test_reminders_branch_skips_already_queued(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = True
        mock_ctx["internal_api"].get.return_value = [
            {"id": 7, "client_email": "x@x.com", "name": "X", "service_name": "S", "datetime": "27.04.2026 10:00", "lang": "de", "master_name": "M"}
        ]
        mock_ctx["arq_service"].enqueue_job.return_value = None  # already in queue

        res = await booking_maintenance_task(mock_ctx)

        assert res == {"status": "ok", "actions": 0}
        mock_ctx["internal_api"].post.assert_not_called()

    async def test_reminders_branch_skips_missing_email(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = True
        mock_ctx["internal_api"].get.return_value = [
            {"id": 5, "client_email": "", "name": "Ghost", "service_name": "S", "datetime": "27.04.2026 12:00", "lang": "de", "master_name": "M"}
        ]

        res = await booking_maintenance_task(mock_ctx)

        assert res == {"status": "ok", "actions": 0}
        mock_ctx["arq_service"].enqueue_job.assert_called_once()  # _schedule_next only

    async def test_reminders_branch_invalid_response(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = True
        mock_ctx["internal_api"].get.return_value = {"error": "unexpected"}

        res = await booking_maintenance_task(mock_ctx)

        assert res == {"status": "ok", "actions": 0}

    async def test_reminders_branch_missing_appt_id(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = True
        mock_ctx["internal_api"].get.return_value = [
            {"client_email": "x@x.com", "name": "X"}  # No 'id'
        ]

        res = await booking_maintenance_task(mock_ctx)
        assert res == {"status": "ok", "actions": 0}

    async def test_reminders_branch_mark_failed(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = True
        mock_ctx["internal_api"].get.return_value = [
            {"id": 1, "client_email": "x@x.com", "name": "X", "service_name": "S", "datetime": "27.04.2026 10:00", "lang": "de", "master_name": "M"}
        ]
        mock_ctx["arq_service"].enqueue_job.return_value = AsyncMock()
        mock_ctx["internal_api"].post.side_effect = Exception("API fail")

        # Should not raise, just log warning and continue
        res = await booking_maintenance_task(mock_ctx)
        assert res == {"status": "ok", "actions": 1}
        mock_ctx["internal_api"].post.assert_called_once()
