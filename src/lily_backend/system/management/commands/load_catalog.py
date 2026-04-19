from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load all modular catalog fixtures (categories, services, conflict rules)"

    def handle(self, *args, **options):
        fixtures = [
            "catalog/categories.json",
            "catalog/services.json",
            "catalog/conflict_rules.json",
            "catalog/booking_settings.json",
        ]

        self.stdout.write("Loading catalog fixtures...")

        for fixture in fixtures:
            self.stdout.write(f"  Loading {fixture}...")
            try:
                call_command("loaddata", fixture)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error loading {fixture}: {e}"))
                return

        self.stdout.write(self.style.SUCCESS("Successfully loaded all catalog fixtures."))
