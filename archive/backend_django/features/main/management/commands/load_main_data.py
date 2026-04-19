from core.logger import log
from django.conf import settings
from django.core.management import call_command
from features.system.management.commands.base_hash_command import HashProtectedCommand


class Command(HashProtectedCommand):
    help = "Load main initial data (categories, services) from fixtures"
    fixture_key = "load_main_data"

    def get_fixture_paths(self) -> list:
        path = settings.BASE_DIR / "features" / "main" / "fixtures" / "initial_categories.json"
        return [path]

    def handle_import(self, *args, **options):
        log.info("Command: load_main_data | Action: Start")

        fixture = settings.BASE_DIR / "features" / "main" / "fixtures" / "initial_categories.json"

        if not fixture.exists():
            log.warning(f"Command: load_main_data | Action: SkipFixture | path={fixture} | reason=NotFound")
            self.stdout.write(self.style.WARNING(f"Fixture not found: {fixture}"))
            return

        log.debug(f"Command: load_main_data | Action: LoadingFixture | path={fixture}")
        try:
            call_command("loaddata", str(fixture))
            log.info(f"Command: load_main_data | Action: Success | path={fixture}")
            self.stdout.write(self.style.SUCCESS(f"Successfully loaded {fixture}"))
        except Exception as e:
            log.error(f"Command: load_main_data | Action: Failed | path={fixture} | error={e}")
            self.stdout.write(self.style.ERROR(f"Error loading {fixture}: {e}"))
            raise

        log.info("Command: load_main_data | Action: Success | status=AllFixturesProcessed")
