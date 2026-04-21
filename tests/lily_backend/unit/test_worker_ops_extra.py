from unittest.mock import MagicMock, patch

import pytest

from src.lily_backend.system.services.worker_ops import WorkerOpsService, _health, _is_docker_only_hostname, _parse_dt


@pytest.mark.unit
class TestWorkerOpsExtra:
    @patch("src.lily_backend.system.services.worker_ops._redis_url")
    @patch("src.lily_backend.system.services.worker_ops.Path")
    def test_build_redis_client_none_outside_docker(self, mock_path, mock_url):
        """Test build_redis_client returns None if hostname is 'redis' and not in Docker."""
        mock_url.return_value = "redis://redis:6379/0"
        mock_path.return_value.exists.return_value = False

        service = WorkerOpsService()
        assert service.redis is None

    def test_list_tasks_error_no_redis(self):
        """Test list_tasks raises RuntimeError if redis is None."""
        service = WorkerOpsService(redis_client=None)
        # Mocking build_redis_client to return None
        with patch.object(service, "_build_redis_client", return_value=None):
            service.redis = None
            with pytest.raises(RuntimeError, match="Redis host 'redis' is only resolvable"):
                service.list_tasks()

    @patch.object(WorkerOpsService, "list_tasks")
    def test_summary_exception_handler(self, mock_list):
        """Test summary handles exceptions from list_tasks."""
        mock_list.side_effect = Exception("test error")
        service = WorkerOpsService(redis_client=MagicMock())

        res = service.summary()
        assert res["status"] == "critical"
        assert res["error"] == "test error"

    def test_set_enabled_no_redis(self):
        """Test set_enabled does nothing if redis is None."""
        service = WorkerOpsService(redis_client=None)
        service.redis = None
        # Should not raise
        service.set_enabled("task", True)

    def test_parse_dt_error_handing(self):
        """Test _parse_dt handles invalid isoformat."""
        assert _parse_dt("invalid-date") is None
        assert _parse_dt("") is None

    @patch("src.lily_backend.system.services.worker_ops.Path")
    def test_is_docker_only_hostname(self, mock_path):
        """Test _is_docker_only_hostname logic."""
        mock_path.return_value.exists.return_value = False
        assert _is_docker_only_hostname("redis://redis:6379/0") is True
        assert _is_docker_only_hostname("redis://localhost:6379/0") is False

        mock_path.return_value.exists.return_value = True
        assert _is_docker_only_hostname("redis://redis:6379/0") is False

    def test_health_branches(self):
        """Test remaining branches in _health."""
        # Disabled
        assert _health({"enabled": "0"}, stale_after=60) == "disabled"
        # High failures
        assert _health({"consecutive_failures": "3"}, stale_after=60) == "critical"
        # Failed status
        assert _health({"last_status": "failed"}, stale_after=60) == "degraded"
        # Not started
        assert _health({}, stale_after=60) == "degraded"
