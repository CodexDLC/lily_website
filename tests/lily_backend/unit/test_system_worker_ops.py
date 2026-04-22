from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from system.services.worker_ops import WorkerOpsService, _health


class TestSystemWorkerOps:
    @pytest.fixture
    def mock_redis(self):
        with patch("system.services.worker_ops.Redis") as mock:
            client = MagicMock()
            mock.from_url.return_value = client
            yield client

    def test_health_logic(self):
        # Case: Disabled
        assert _health({"enabled": "0"}, stale_after=60) == "disabled"

        # Case: Critical due to failures
        assert _health({"consecutive_failures": "3"}, stale_after=60) == "critical"

        # Case: Degraded due to last status
        assert _health({"last_status": "failed"}, stale_after=60) == "degraded"

        # Case: Critical due to staleness
        now = datetime.now(UTC)
        stale_time = (now - timedelta(seconds=120)).isoformat()
        assert _health({"last_started_at": stale_time}, stale_after=60) == "critical"

        # Case: Healthy
        recent_time = (now - timedelta(seconds=10)).isoformat()
        assert _health({"last_started_at": recent_time}, stale_after=60) == "healthy"

        # Case: Degraded if never started
        assert _health({}, stale_after=60) == "degraded"

    def test_list_tasks(self, mock_redis):
        service = WorkerOpsService(redis_client=mock_redis)
        mock_redis.scan_iter.return_value = ["worker:tasks:t1", "worker:tasks:t2"]
        mock_redis.hgetall.side_effect = [{"task_id": "t1", "enabled": "1"}, {"task_id": "t2", "enabled": "0"}]

        tasks = service.list_tasks()
        assert len(tasks) == 2
        assert tasks[0].task_id == "t1"
        assert tasks[1].enabled is False

    def test_summary(self, mock_redis):
        service = WorkerOpsService(redis_client=mock_redis)
        mock_redis.scan_iter.return_value = ["worker:tasks:t1"]
        mock_redis.hgetall.return_value = {"task_id": "t1", "consecutive_failures": "3"}

        summary = service.summary()
        assert summary["total"] == 1
        assert summary["critical"] == 1
        assert summary["status"] == "critical"

    def test_enqueue_now(self):
        with patch("core.arq.client.arq_client") as mock_arq:
            service = WorkerOpsService(redis_client=MagicMock())
            # Use a valid task from TASK_FUNCTIONS (e.g., booking.worker)
            service.enqueue_now("booking.worker")

            mock_arq.enqueue.assert_called_once()
            args, kwargs = mock_arq.enqueue.call_args
            assert args[0] == "booking_maintenance_task"
            assert kwargs["job_id"] == "booking.worker:manual"

    def test_enqueue_now_invalid_task(self):
        service = WorkerOpsService(redis_client=MagicMock())
        result = service.enqueue_now("non-existent")
        assert result is None
