from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

from src.lily_backend.cabinet.views.ops import WorkerOpsView


@pytest.mark.unit
class TestWorkerOpsViewExtended:
    def setup_method(self):
        self.factory = RequestFactory()
        self.view = WorkerOpsView()

    @patch("src.lily_backend.cabinet.views.ops.WorkerOpsService")
    @patch("src.lily_backend.cabinet.views.ops.redirect")
    def test_worker_ops_post_actions(self, mock_redirect, mock_service_class):
        """Test various POST actions in WorkerOpsView."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        actions = [
            ("enable", True),
            ("disable", False),
            ("run_now", None),
            ("reschedule", None),
        ]

        for action, _value in actions:
            request = self.factory.post("/ops/", {"action": action, "task_id": "test_task"})
            self.view.post(request)

            if action == "enable":
                mock_service.set_enabled.assert_called_with("test_task", True)
            elif action == "disable":
                mock_service.set_enabled.assert_called_with("test_task", False)
            elif action == "run_now":
                mock_service.enqueue_now.assert_called_with("test_task")
            elif action == "reschedule":
                mock_service.enqueue_now.assert_called_with("test_task", defer_by=60)

        assert mock_redirect.call_count == 4
        mock_redirect.assert_called_with("cabinet:ops_workers")
