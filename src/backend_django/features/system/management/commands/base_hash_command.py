import contextlib

from django.core.management.base import BaseCommand
from django.db import OperationalError, connection
from features.system.models.fixture_version import FixtureVersion
from features.system.utils.fixture_hash import compute_paths_hash


class HashProtectedCommand(BaseCommand):
    fixture_key = None  # переопределяется в наследнике

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Ignore hash check and force update")

    def get_fixture_paths(self) -> list:
        """Возвращает список Path к файлам фикстур."""
        raise NotImplementedError

    def handle_import(self, *args, **options):
        """Основная логика команды."""
        raise NotImplementedError

    def handle(self, *args, **options):
        if not self.fixture_key:
            raise ValueError("fixture_key is not set")

        paths = [p for p in self.get_fixture_paths() if p.is_file()]
        if not paths:
            self.stdout.write(self.style.WARNING(f"Skipped {self.fixture_key}: No fixtures found."))
            return

        current_hash = compute_paths_hash(paths)
        force = options.get("force", False)

        # Check if table exists (crucial for initial docker run)
        table_exists = "system_fixtureversion" in connection.introspection.table_names()

        if not force and table_exists:
            with contextlib.suppress(FixtureVersion.DoesNotExist, OperationalError):
                # Fallback if anything goes wrong with the DB check
                record, _ = FixtureVersion.objects.get_or_create(name=self.fixture_key, defaults={"content_hash": ""})
                if record.content_hash == current_hash:
                    self.stdout.write(f"Skipped {self.fixture_key}: fixture hash unchanged.")
                    return

        # Execute the actual import logic
        self.handle_import(*args, **options)

        # Update hash if table exists
        if table_exists:
            with contextlib.suppress(OperationalError):
                FixtureVersion.objects.update_or_create(name=self.fixture_key, defaults={"content_hash": current_hash})
