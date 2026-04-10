from typing import ClassVar

from codex_django.system.management.base_commands import BaseUpdateAllContentCommand
from django.core.management import call_command


class Command(BaseUpdateAllContentCommand):
    """
    Run all content update commands and clear cache.
    Useful to run during entrypoint initialization or deployments.
    """

    help = "Run all content update commands and clear cache"

    commands_to_run: ClassVar[list[str]] = [
        "update_site_settings",
        "update_static_translations",
        "update_email_content",
        "update_seo",
    ]

    def handle(self, *args, **options):
        # Site Settings
        self.stdout.write("\n--- Updating Site Settings ---")
        call_command("update_site_settings")

        # Static Translations
        self.stdout.write("\n--- Updating Static Translations ---")
        call_command("update_static_translations")

        # Email Content
        self.stdout.write("\n--- Updating Email Content ---")
        call_command("update_email_content")

        # SEO
        self.stdout.write("\n--- Updating Static Page SEO ---")
        call_command("update_seo")

        self.stdout.write(self.style.SUCCESS("\nAll content updates completed."))
