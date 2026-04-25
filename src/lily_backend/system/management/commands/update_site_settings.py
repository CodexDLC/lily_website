from codex_django.system.management import SingletonFixtureUpdateCommand
from django.conf import settings


class Command(SingletonFixtureUpdateCommand):
    help = "Update Site Settings from JSON fixture (system/fixtures/content/site_settings.json)"
    fixture_key = "site_settings"
    fixture_path = settings.BASE_DIR / "system" / "fixtures" / "content" / "site_settings.json"
    model_path = "system.SiteSettings"

    def handle(self, *args, **options):
        super().handle(*args, **options)

        # After fixture is loaded, sync site_base_url from ENV
        from system.models import SiteSettings

        site_base_url = getattr(settings, "SITE_BASE_URL", "").rstrip("/") + "/"
        if site_base_url and site_base_url != "/":
            settings_obj = SiteSettings.load()
            if settings_obj.site_base_url != site_base_url:
                settings_obj.site_base_url = site_base_url
                settings_obj.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully synced SITE_BASE_URL from ENV to DB: {site_base_url}")
                )
