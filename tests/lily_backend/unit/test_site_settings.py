from unittest.mock import MagicMock, patch
import pytest
from src.lily_backend.system.services.site_settings import SiteSettingsService

@pytest.mark.unit
class TestSiteSettingsService:
    @patch("codex_django.cabinet.services.site_settings.SiteSettingsService.save_context")
    def test_save_context_delegation(self, mock_save):
        """Test save_context delegates to library service."""
        request = MagicMock()
        mock_save.return_value = (True, "Success")

        res = SiteSettingsService.save_context(request)
        assert res == (True, "Success")

    @patch("codex_django.cabinet.services.site_settings.SiteSettingsService.get_context")
    @patch("features.notifications.models.NotificationRecipient.objects.all")
    def test_get_context_delegation(self, mock_recipients, mock_get):
        """Test get_context delegates to library service."""
        request = MagicMock()
        mock_get.return_value = {"tabs": []}
        mock_recipients.return_value.order_by.return_value = []

        res = SiteSettingsService.get_context(request)

        assert "tabs" in res
        assert "recipients" in res
