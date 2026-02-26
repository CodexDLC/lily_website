from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all content update commands and clear cache"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(">>> Updating Site Settings..."))
        call_command("update_site_settings")

        self.stdout.write(self.style.MIGRATE_HEADING("\n>>> Updating Static Translations (DB Content)..."))
        call_command("update_static_translations")

        self.stdout.write(self.style.MIGRATE_HEADING("\n>>> Updating Services SEO..."))
        call_command("update_services_seo")

        self.stdout.write(self.style.MIGRATE_HEADING("\n>>> Updating Static Pages SEO..."))
        call_command("update_static_seo")

        self.stdout.write(self.style.MIGRATE_HEADING("\n>>> Loading Main App Initial Data (Categories)..."))
        call_command("load_main_data")

        self.stdout.write(self.style.MIGRATE_HEADING("\n>>> Loading / Updating Services from System Fixtures..."))
        call_command("load_services")

        self.stdout.write(self.style.MIGRATE_HEADING("\n>>> Updating Masters Content..."))
        call_command("update_masters")

        self.stdout.write(self.style.SUCCESS("\nAll updates completed. Cache invalidated selectively per change."))
