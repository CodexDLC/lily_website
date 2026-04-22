from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

from src.lily_backend.cabinet.context_processors import (
    _get_default_staff_module,
    _hide_tracking_widgets_on_business_stats,
    _is_client_cabinet_path,
    bell_notifications,
    cabinet,
    notifications,
)


@pytest.mark.unit
class TestCabinetContextProcessors:
    def setup_method(self):
        self.factory = RequestFactory()
        self.user = MagicMock()
        self.user.is_authenticated = True

    def test_get_default_staff_module(self):
        """Test _get_default_staff_module helper."""
        with patch("src.lily_backend.cabinet.context_processors.cabinet_registry") as mock_registry:
            mock_registry.get_default_module.return_value = "staff_module"
            assert _get_default_staff_module() == "staff_module"

    def test_is_client_cabinet_path(self):
        """Test _is_client_cabinet_path helper."""
        request = MagicMock()
        request.path = "/cabinet/my/profile"
        assert _is_client_cabinet_path(request) is True

        request.path = "/cabinet/other"
        assert _is_client_cabinet_path(request) is False

        request.path = "/cabinet/my"
        assert _is_client_cabinet_path(request) is True

    def test_hide_tracking_widgets_on_business_stats(self):
        """Test widget filtering on business_stats module."""
        # Case 1: Not business_stats
        context = {"cabinet_active_module": "other", "cabinet_dashboard_widgets": [1, 2]}
        _hide_tracking_widgets_on_business_stats(context)
        assert len(context["cabinet_dashboard_widgets"]) == 2

        # Case 2: Business stats with tracking widgets
        mock_widget_1 = MagicMock()
        mock_widget_1.context_key = "tracking_stats"
        mock_widget_2 = MagicMock()
        mock_widget_2.context_key = "other_stats"

        context = {
            "cabinet_active_module": "business_stats",
            "cabinet_dashboard_widgets": [mock_widget_1, mock_widget_2],
        }
        _hide_tracking_widgets_on_business_stats(context)
        assert len(context["cabinet_dashboard_widgets"]) == 1
        assert context["cabinet_dashboard_widgets"][0] == mock_widget_2

    @patch("src.lily_backend.cabinet.context_processors.base_cabinet")
    @patch("src.lily_backend.cabinet.context_processors.cabinet_registry")
    def test_cabinet_processor_client_space(self, mock_registry, mock_base_cabinet):
        """Test cabinet processor logic for client space."""
        request = self.factory.get("/cabinet/my/")
        request.user = self.user
        request.cabinet_space = "client"

        mock_base_cabinet.return_value = {"existing": "data"}
        mock_registry.get_sidebar.return_value = ["sidebar"]

        context = cabinet(request)

        assert context["cabinet_space"] == "client"
        assert context["existing"] == "data"
        assert context["cabinet_sidebar"] == ["sidebar"]

    @patch("src.lily_backend.cabinet.context_processors.base_cabinet")
    @patch("src.lily_backend.cabinet.context_processors.cabinet_registry")
    def test_cabinet_processor_staff_admin_fallback(self, mock_registry, mock_base_cabinet):
        """Test cabinet processor fallback to default staff module for admin module."""
        request = self.factory.get("/cabinet/staff/")
        request.user = self.user

        # Base cabinet says staff admin but no sidebar
        mock_base_cabinet.return_value = {
            "cabinet_space": "staff",
            "cabinet_active_module": "admin",
            "cabinet_sidebar": None,
        }

        mock_registry.get_default_module.return_value = "staff_dashboard"
        mock_registry.get_sidebar.return_value = ["staff_sidebar"]

        context = cabinet(request)

        assert context["cabinet_active_module"] == "staff_dashboard"
        assert context["cabinet_sidebar"] == ["staff_sidebar"]

    @patch("src.lily_backend.cabinet.context_processors.notification_registry")
    def test_notifications_processors(self, mock_registry):
        """Test notifications and bell_notifications processors."""
        request = self.factory.get("/")
        mock_registry.get_items.return_value = ["notif1"]

        res1 = notifications(request)
        assert res1["notification_items"] == ["notif1"]

        res2 = bell_notifications(request)
        assert res2["bell_items"] == ["notif1"]
