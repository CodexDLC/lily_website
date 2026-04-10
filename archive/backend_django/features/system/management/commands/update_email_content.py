import json
import os

from core.logger import log
from django.conf import settings
from features.system.management.commands.base_hash_command import HashProtectedCommand
from features.system.models.email_content import EmailContent


class Command(HashProtectedCommand):
    help = "Update email content blocks from fixture with translations"
    fixture_key = "update_email_content"

    def get_fixture_paths(self) -> list:
        path = settings.BASE_DIR / "features" / "system" / "fixtures" / "initial_email_content.json"
        return [path]

    def handle_import(self, *args, **options):
        log.info("Command: update_email_content | Action: Start")

        fixture_path = os.path.join(settings.BASE_DIR, "features", "system", "fixtures", "initial_email_content.json")

        if not os.path.exists(fixture_path):
            log.error(f"Command: update_email_content | Error: Fixture not found at {fixture_path}")
            return

        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                fields = item["fields"]

                # Prepare defaults including translations if they exist in JSON
                defaults = {
                    "category": fields["category"],
                    "description": fields.get("description", ""),
                }

                # Map translations from JSON to model fields
                if "text_de" in fields:
                    defaults["text_de"] = fields["text_de"]
                if "text_ru" in fields:
                    defaults["text_ru"] = fields["text_ru"]
                if "text_en" in fields:
                    defaults["text_en"] = fields["text_en"]

                # Fallback for base text field if no translations
                if "text" in fields:
                    defaults["text"] = fields["text"]

                EmailContent.objects.update_or_create(key=fields["key"], defaults=defaults, create_defaults=defaults)

            log.info(f"Command: update_email_content | Action: Success | Updated: {len(data)}")
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated {len(data)} email content blocks with translations.")
            )

        except Exception as e:
            log.error(f"Command: update_email_content | Action: Failed | Error: {e}")
            raise e
