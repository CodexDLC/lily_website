import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load main initial data (categories, services) from fixtures"

    def handle(self, *args, **options):
        # Fixtures to load in order
        fixtures = [
            "features/main/fixtures/initial_categories.json",
        ]

        for fixture in fixtures:
            if not os.path.exists(fixture):
                self.stdout.write(self.style.WARNING(f"Fixture not found: {fixture}"))
                continue

            self.stdout.write(f"Loading data from {fixture}...")
            try:
                call_command("loaddata", fixture)
                self.stdout.write(self.style.SUCCESS(f"Successfully loaded {fixture}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error loading {fixture}: {e}"))
