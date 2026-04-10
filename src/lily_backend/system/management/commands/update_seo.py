import json

from codex_django.system.management.base_commands import BaseHashProtectedCommand
from django.conf import settings
from loguru import logger as log

from system.models.seo import StaticPageSeo


class Command(BaseHashProtectedCommand):
    """
    Management command to update Static Page SEO from JSON fixture.
    Checks a hash to avoid double loading.
    Usage: python manage.py update_seo
    """

    help = "Update Static Page SEO from JSON fixture (system/fixtures/seo/static_pages_seo.json)"
    fixture_key = "static_pages_seo"

    def get_fixture_paths(self):
        return [settings.BASE_DIR / "system" / "fixtures" / "seo" / "static_pages_seo.json"]

    def handle_import(self, *args, **options):
        log.info("Command: update_seo | Action: Start")

        fixture_paths = self.get_fixture_paths()
        if not fixture_paths:
            return False

        fixture_path = fixture_paths[0]
        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            log.error(f"Command: update_seo | Action: Failed | error=JSONDecodeError | message={e}")
            self.stdout.write(self.style.ERROR(f"Error decoding JSON: {e}"))
            return False

        if not data or not isinstance(data, list):
            log.error("Command: update_seo | Action: Failed | error=Invalid format")
            self.stdout.write(self.style.ERROR("Invalid fixture format"))
            return False

        self.stdout.write(f"Processing {len(data)} SEO items...")

        updated_count = 0
        created_count = 0

        for item in data:
            fields = item.get("fields", {})
            page_key = fields.get("page_key")
            if not page_key:
                continue

            instance, created = StaticPageSeo.objects.update_or_create(page_key=page_key, defaults=fields)

            if created:
                created_count += 1
                log.debug(f"Action: Create | page_key={page_key}")
            else:
                updated_count += 1
                log.debug(f"Action: Update | page_key={page_key}")

        log.info(f"Command: update_seo | Action: Success | created={created_count} | updated={updated_count}")
        self.stdout.write(
            self.style.SUCCESS(f"✓ Static Page SEO updated: {created_count} created, {updated_count} updated")
        )

        return True
