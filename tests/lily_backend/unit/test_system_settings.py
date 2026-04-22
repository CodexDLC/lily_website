from system.services.site_settings import SiteSettingsService


class TestSystemSettings:
    def test_tabs_configuration(self):
        tabs = SiteSettingsService.TABS_CONFIG

        # Verify custom Lily tabs are present
        assert "general" in tabs
        assert "work_hours" in tabs
        assert "hiring" in tabs
        assert "technical" in tabs

        # Verify labels (translations will be lazily evaluated strings or proxies)
        assert tabs["general"]["icon"] == "bi-info-circle"
        assert tabs["work_hours"]["icon"] == "bi-clock"
        assert tabs["technical"]["icon"] == "bi-tools"
