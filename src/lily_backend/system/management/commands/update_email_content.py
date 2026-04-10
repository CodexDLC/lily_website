import json

from codex_django.system.management.base_commands import BaseHashProtectedCommand
from django.conf import settings
from loguru import logger as log

from system.models.email_content import EmailContent


class Command(BaseHashProtectedCommand):
    """
    Management command to update Email Content from JSON fixture.
    Checks a hash to avoid double loading.
    Usage: python manage.py update_email_content
    """

    help = "Update Email Content from JSON fixture (system/fixtures/content/email_content.json)"
    fixture_key = "email_content"

    def get_fixture_paths(self):
        return [settings.BASE_DIR / "system" / "fixtures" / "content" / "email_content.json"]

    def handle_import(self, *args, **options):
        log.info("Command: update_email_content | Action: Start")

        fixture_paths = self.get_fixture_paths()
        if not fixture_paths:
            return False

        fixture_path = fixture_paths[0]
        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            log.error(f"Command: update_email_content | Action: Failed | error=JSONDecodeError | message={e}")
            self.stdout.write(self.style.ERROR(f"Error decoding JSON: {e}"))
            return False

        if not data or not isinstance(data, list):
            log.error("Command: update_email_content | Action: Failed | error=Invalid format")
            self.stdout.write(self.style.ERROR("Invalid fixture format"))
            return False

        self.stdout.write(f"Processing {len(data)} email content items...")

        updated_count = 0
        created_count = 0

        for item in data:
            fields = item.get("fields", {})
            key = fields.get("key")
            if not key:
                continue

            instance, created = EmailContent.objects.update_or_create(key=key, defaults=fields)

            if created:
                created_count += 1
                log.debug(f"Action: Create | key={key}")
            else:
                updated_count += 1
                log.debug(f"Action: Update | key={key}")

        log.info(f"Command: update_email_content | Action: Success | created={created_count} | updated={updated_count}")
        self.stdout.write(
            self.style.SUCCESS(f"✓ Email Content updated: {created_count} created, {updated_count} updated")
        )

        return True
