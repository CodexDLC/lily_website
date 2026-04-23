from codex_django.cache.values import CacheCoder
from system.models import SiteSettings


def test_project_site_settings_to_dict_keeps_native_values():
    settings = SiteSettings(hiring_active=False, app_mode_enabled=True, maintenance_mode=False)

    data = settings.to_dict()

    assert data["hiring_active"] is False
    assert data["app_mode_enabled"] is True
    assert data["maintenance_mode"] is False


def test_cache_coder_handles_project_settings_values():
    settings = SiteSettings(hiring_active=True, app_mode_enabled=False)
    coded = {key: CacheCoder.dump(value) for key, value in settings.to_dict().items()}

    assert coded["hiring_active"] == "1"
    assert coded["app_mode_enabled"] == "0"
