import os

from core.logger import log
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load main initial data (categories, services) from fixtures"

    def handle(self, *args, **options):
        log.info("Command: load_main_data | Action: Start")

        # Fixtures to load in order
        fixtures = [
            "features/main/fixtures/initial_categories.json",
        ]

        for fixture in fixtures:
            if not os.path.exists(fixture):
                log.warning(f"Command: load_main_data | Action: SkipFixture | path={fixture} | reason=NotFound")
                self.stdout.write(self.style.WARNING(f"Fixture not found: {fixture}"))
                continue

            log.debug(f"Command: load_main_data | Action: LoadingFixture | path={fixture}")
            try:
                call_command("loaddata", fixture)
                log.info(f"Command: load_main_data | Action: Success | path={fixture}")
                self.stdout.write(self.style.SUCCESS(f"Successfully loaded {fixture}"))
            except Exception as e:
                log.error(f"Command: load_main_data | Action: Failed | path={fixture} | error={e}")
                self.stdout.write(self.style.ERROR(f"Error loading {fixture}: {e}"))
                raise

        log.info("Command: load_main_data | Action: Success | status=AllFixturesProcessed")
