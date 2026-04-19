from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from workers.system_worker.tasks.tracking import flush_tracking_task


@pytest.fixture
def mock_ctx():
    settings = MagicMock()
    settings.tracking_flush_interval_sec = 60
    settings.tracking_flush_stale_after_sec = 120
    settings.tracking_worker_api_key = "secret-key"  # pragma: allowlist secret

    internal_api = AsyncMock()
    heartbeat_registry = AsyncMock()
    heartbeat_registry.should_run.return_value = True

    return {
        "settings": settings,
        "internal_api": internal_api,
        "heartbeat_registry": heartbeat_registry,
        "job_id": "job-123",
    }


class TestTrackingFlushTask:
    @pytest.mark.asyncio
    async def test_flush_tracking_task_success(self, mock_ctx):
        mock_ctx["internal_api"].post.return_value = {"status": "flushed"}

        result = await flush_tracking_task(mock_ctx, payload={})

        assert result == {"status": "flushed"}
        mock_ctx["internal_api"].post.assert_called_once_with(
            "/v1/tracking/flush",
            scope="tracking.flush",
            token="secret-key",  # pragma: allowlist secret
        )
        mock_ctx["heartbeat_registry"].mark_started.assert_called_once()
        mock_ctx["heartbeat_registry"].mark_finished.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_tracking_task_skipped(self, mock_ctx):
        mock_ctx["heartbeat_registry"].should_run.return_value = False

        result = await flush_tracking_task(mock_ctx)

        assert result is None
        mock_ctx["internal_api"].post.assert_not_called()
        mock_ctx["heartbeat_registry"].mark_finished.assert_called_once_with(ANY, status="skipped")
