import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run operational legacy imports only (users, clients, appointments)"

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, help="Legacy PostgreSQL connection URL")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes")

    def handle(self, *args, **options):
        url = options["url"] or os.environ.get("LEGACY_DATABASE_URL")
        if not url:
            self.stdout.write(self.style.ERROR("Must provide --url or set LEGACY_DATABASE_URL env var"))
            return

        dry_run = options["dry_run"]

        self.stdout.write(self.style.MIGRATE_HEADING("--- Starting Operational Legacy Import ---"))

        self.stdout.write(self.style.MIGRATE_LABEL("\n0. Migrating Users (Superusers/Staff)..."))
        call_command("migrate_users", url=url, dry_run=dry_run)

        self.stdout.write(self.style.MIGRATE_LABEL("\n1. Migrating Clients..."))
        call_command("migrate_clients", url=url, dry_run=dry_run)

        self.stdout.write(self.style.MIGRATE_LABEL("\n2. Migrating Appointments..."))
        call_command("migrate_appointments", url=url, dry_run=dry_run)

        self.stdout.write(self.style.SUCCESS("\n--- Operational legacy import completed ---"))
