from codex_django.system.management import SingletonFixtureUpdateCommand
from django.conf import settings


class Command(SingletonFixtureUpdateCommand):
    help = "Update Site Settings from JSON fixture (system/fixtures/content/site_settings.json)"
    fixture_key = "site_settings"
    fixture_path = settings.BASE_DIR / "system" / "fixtures" / "content" / "site_settings.json"
    model_path = "system.SiteSettings"
