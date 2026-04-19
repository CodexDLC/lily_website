import os
import sqlite3

import psycopg2
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from psycopg2.extras import RealDictCursor

from system.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Migrate superusers and staff from legacy sqlite or postgres database"

    def add_arguments(self, parser):
        parser.add_argument("--db", type=str, help="Path to legacy sqlite db")
        parser.add_argument("--url", type=str, help="PostgreSQL connection URL")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes")

    def handle(self, *args, **options):
        db_url = options["url"] or os.environ.get("LEGACY_DATABASE_URL")
        db_path = options["db"]

        if db_url:
            self.stdout.write(f"Connecting to PostgreSQL: {db_url[:30]}...")
            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
        elif db_path:
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(os.path.join(os.getcwd(), db_path))
            if not os.path.exists(db_path):
                self.stdout.write(self.style.ERROR(f"Legacy database not found at {db_path}"))
                return
            self.stdout.write(f"Connecting to SQLite: {db_path}...")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        else:
            self.stdout.write(self.style.ERROR("Must provide --db (sqlite) or --url (postgres)"))
            return

        try:
            # First try standard truth literal
            cursor.execute("SELECT * FROM auth_user WHERE is_superuser = TRUE OR is_staff = TRUE")
            legacy_users = cursor.fetchall()
        except Exception:
            try:
                # Fallback for SQLite/different dialects
                cursor.execute("SELECT * FROM auth_user WHERE is_superuser = 1 OR is_staff = 1")
                legacy_users = cursor.fetchall()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading legacy table: {e}"))
                return

        self.stdout.write(f"Found {len(legacy_users)} legacy superusers/staff.")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for row in legacy_users:
            username = row["username"]
            email = row.get("email") or ""

            # Standard Django user lookup
            user = User.objects.filter(username=username).first()
            if not user and email:
                user = User.objects.filter(email=email).first()

            if user:
                action = "Updating"
            else:
                action = "Creating"
                user = User(username=username)

            user.email = email
            user.first_name = row.get("first_name") or ""
            user.last_name = row.get("last_name") or ""
            user.is_superuser = bool(row["is_superuser"])
            user.is_staff = bool(row["is_staff"])
            user.is_active = bool(row.get("is_active", True))

            # Transfer password hash directly
            user.password = row["password"]

            if not options["dry_run"]:
                try:
                    with transaction.atomic():
                        user.save()

                        # Migration Sticking (Linking)
                        # 1. Ensure allauth EmailAddress exists and is verified
                        if user.email:
                            EmailAddress.objects.get_or_create(
                                user=user,
                                email=user.email,
                                defaults={"verified": True, "primary": True},
                            )

                        # 2. Ensure UserProfile exists
                        UserProfile.objects.get_or_create(user=user)

                    if action == "Creating":
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error saving {username}: {e}"))
                    skipped_count += 1
                    continue
            else:
                if action == "Creating":
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(f"  {action} user: {username} ({'Superuser' if user.is_superuser else 'Staff'})")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run - no changes saved."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration complete. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )

        conn.close()
