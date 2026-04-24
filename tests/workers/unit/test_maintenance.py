from unittest.mock import AsyncMock, MagicMock

import pytest

from src.workers.system_worker.tasks.maintenance import ensure_tasks_scheduled, system_watchdog_task


@pytest.fixture
def mock_ctx():
    return {
        "arq_service": AsyncMock(),
    }


@pytest.mark.asyncio
class TestMaintenanceTasks:
    async def test_ensure_tasks_scheduled_success(self, mock_ctx):
        mock_ctx["arq_service"].enqueue_job.return_value = MagicMock()

        await ensure_tasks_scheduled(mock_ctx)

        assert mock_ctx["arq_service"].enqueue_job.call_count == 3
        # Check one of the calls
        mock_ctx["arq_service"].enqueue_job.assert_any_call(
            "import_emails_task", _job_id="conversations.import:next", _queue_name="system"
        )

    async def test_ensure_tasks_scheduled_no_arq(self):
        ctx = {}
        await ensure_tasks_scheduled(ctx)
        # Should return without error (coverage for lines 7-9)

    async def test_ensure_tasks_scheduled_already_enqueued(self, mock_ctx):
        mock_ctx["arq_service"].enqueue_job.return_value = None

        await ensure_tasks_scheduled(mock_ctx)

        assert mock_ctx["arq_service"].enqueue_job.call_count == 3

    async def test_ensure_tasks_scheduled_exception(self, mock_ctx):
        mock_ctx["arq_service"].enqueue_job.side_effect = Exception("ARQ error")

        # Should not raise exception but log it
        await ensure_tasks_scheduled(mock_ctx)

        assert mock_ctx["arq_service"].enqueue_job.call_count == 3

    async def test_system_watchdog_task(self, mock_ctx):
        mock_ctx["arq_service"].enqueue_job.return_value = MagicMock()

        await system_watchdog_task(mock_ctx)

        assert mock_ctx["arq_service"].enqueue_job.call_count == 3
