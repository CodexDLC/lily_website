"""
Management command to update Site Settings from JSON fixture.
Usage: python manage.py update_site_settings
"""

import json

from core.logger import log
from django.conf import settings
from django.core.management.base import BaseCommand
from features.system.models import SiteSettings


class Command(BaseCommand):
    help = "Update Site Settings from JSON fixture (features/system/fixtures/content/site_settings.json)"

    def handle(self, *args, **options):
        log.info("Command: update_site_settings | Action: Start")

        # Path to fixture
        fixture_path = settings.BASE_DIR / "features" / "system" / "fixtures" / "content" / "site_settings.json"
        log.debug(f"Command: update_site_settings | Action: LoadFixture | path={fixture_path}")

        if not fixture_path.exists():
            log.error(f"Command: update_site_settings | Action: Failed | error=Fixture not found | path={fixture_path}")
            self.stdout.write(self.style.ERROR(f"Fixture not found: {fixture_path}"))
            return

        # Load JSON
        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            log.error(f"Command: update_site_settings | Action: Failed | error=JSONDecodeError | message={e}")
            self.stdout.write(self.style.ERROR(f"Error decoding JSON: {e}"))
            return

        if not data or not isinstance(data, list) or len(data) == 0:
            log.error("Command: update_site_settings | Action: Failed | error=Invalid fixture format")
            self.stdout.write(self.style.ERROR("Invalid fixture format"))
            return

        fixture_data = data[0]["fields"]

        # Load current settings
        site_settings = SiteSettings.load()

        # Compare and update
        updated_fields = []
        for field_name, new_value in fixture_data.items():
            if hasattr(site_settings, field_name):
                current_value = getattr(site_settings, field_name)

                # Convert Decimal fields to string for comparison
                if hasattr(current_value, "__str__") and field_name in ["latitude", "longitude"]:
                    current_value = str(current_value)

                if str(current_value) != str(new_value):
                    setattr(site_settings, field_name, new_value)
                    updated_fields.append(field_name)
                    log.debug(
                        f"Command: update_site_settings | Action: FieldUpdate | field={field_name} | value={new_value}"
                    )
                    self.stdout.write(self.style.SUCCESS(f"  [UPDATE] {field_name}: {new_value}"))

        # Save if there are changes
        if updated_fields:
            site_settings.save()
            log.info(f"Command: update_site_settings | Action: SaveDB | updated_count={len(updated_fields)}")

            # Update Redis cache with new values
            try:
                from features.system.redis_managers.site_settings_manager import SiteSettingsManager

                SiteSettingsManager.save_to_redis(site_settings)
                log.info("Command: update_site_settings | Action: SaveRedis | status=Success")
                self.stdout.write(self.style.SUCCESS("  Redis cache updated."))
            except Exception as e:
                log.error(f"Command: update_site_settings | Action: SaveRedis | status=Failed | error={e}")
                self.stdout.write(self.style.WARNING(f"  Could not update Redis cache: {e}"))

            self.stdout.write(self.style.SUCCESS(f"\n✓ Site Settings updated ({len(updated_fields)} fields changed)"))
        else:
            log.info("Command: update_site_settings | Action: NoChanges")
            self.stdout.write(self.style.SUCCESS("\n✓ No changes needed (all fields up to date)"))

        log.info("Command: update_site_settings | Action: Success")
