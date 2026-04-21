from unittest.mock import MagicMock, patch

import pytest

from src.lily_backend.system.services.site_settings import SiteSettingsService


@pytest.mark.unit
class TestSiteSettingsService:
    @patch("src.lily_backend.system.services.site_settings.LibrarySiteSettingsService")
    def test_save_context_delegation(self, mock_lib_service):
        """Test save_context delegates to library service."""
        request = MagicMock()
        mock_lib_service.save_context.return_value = (True, "success")

        res = SiteSettingsService.save_context(request)

        assert res == (True, "success")
        mock_lib_service.save_context.assert_called_once_with(request)

    @patch("src.lily_backend.system.services.site_settings.LibrarySiteSettingsService")
    def test_get_context_delegation(self, mock_lib_service):
        """Test get_context delegates to library service."""
        request = MagicMock()
        mock_lib_service.get_context.return_value = {"key": "value"}

        res = SiteSettingsService.get_context(request)

        assert res == {"key": "value"}
        mock_lib_service.get_context.assert_called_once_with(request)
