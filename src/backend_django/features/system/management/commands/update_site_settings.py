"""
Management command to update Site Settings from JSON fixture.
Usage: python manage.py update_site_settings
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from features.system.models import SiteSettings


class Command(BaseCommand):
    help = "Update Site Settings from JSON fixture (features/system/fixtures/content/site_settings.json)"

    def handle(self, *args, **options):
        # Path to fixture
        fixture_path = settings.BASE_DIR / "features" / "system" / "fixtures" / "content" / "site_settings.json"

        if not fixture_path.exists():
            self.stdout.write(self.style.ERROR(f"Fixture not found: {fixture_path}"))
            return

        # Load JSON
        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Error decoding JSON: {e}"))
            return

        if not data or not isinstance(data, list) or len(data) == 0:
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
                    self.stdout.write(self.style.SUCCESS(f"  [UPDATE] {field_name}: {new_value}"))

        # Save if there are changes
        if updated_fields:
            site_settings.save()
            self.stdout.write(self.style.SUCCESS(f"\n✓ Site Settings updated ({len(updated_fields)} fields changed)"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ No changes needed (all fields up to date)"))

        # Show Analytics status
        self.stdout.write(self.style.MIGRATE_HEADING("\nAnalytics & Marketing:"))
        self.stdout.write(f"  GA4: {site_settings.google_analytics_id or '(not set)'}")
        self.stdout.write(f"  GTM: {site_settings.google_tag_manager_id or '(not set)'}")
