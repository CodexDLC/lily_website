import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all legacy migration commands (categories, services, clients, masters, appointments)"

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, help="Legacy PostgreSQL connection URL")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes")
        parser.add_argument("--skip-images", action="store_true", help="Do not overwrite category image/icon paths")
        parser.add_argument("--keep-status", action="store_true", help="Do not overwrite category is_planned status")

    def handle(self, *args, **options):
        url = options["url"] or os.environ.get("LEGACY_DATABASE_URL")
        if not url:
            self.stdout.write(self.style.ERROR("Must provide --url or set LEGACY_DATABASE_URL env var"))
            return

        dry_run = options["dry_run"]

        self.stdout.write(self.style.MIGRATE_HEADING("--- Starting Full Legacy Migration ---"))

        self.stdout.write(self.style.MIGRATE_LABEL("\n0. Migrating Users (Superusers/Staff)..."))
        call_command("migrate_users", url=url, dry_run=dry_run)

        self.stdout.write(self.style.MIGRATE_LABEL("\n1. Migrating Categories..."))
        call_command(
            "migrate_categories",
            url=url,
            dry_run=dry_run,
            skip_images=options["skip_images"],
            keep_status=options["keep_status"],
        )

        self.stdout.write(self.style.MIGRATE_LABEL("\n2. Migrating Services..."))
        call_command("migrate_services", url=url, dry_run=dry_run)

        self.stdout.write(self.style.MIGRATE_LABEL("\n3. Migrating Clients..."))
        call_command("migrate_clients", url=url, dry_run=dry_run)

        self.stdout.write(self.style.MIGRATE_LABEL("\n4. Migrating Masters..."))
        call_command("migrate_masters", url=url, dry_run=dry_run)

        self.stdout.write(self.style.MIGRATE_LABEL("\n5. Migrating Appointments..."))
        call_command("migrate_appointments", url=url, dry_run=dry_run)

        self.stdout.write(self.style.SUCCESS("\n--- All legacy migrations completed ---"))
