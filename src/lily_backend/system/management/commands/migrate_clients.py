import os
import sqlite3

import psycopg2
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware
from psycopg2.extras import RealDictCursor

from system.models import Client

User = get_user_model()


class Command(BaseCommand):
    help = "Migrate clients from legacy sqlite or postgres database"

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
            cursor.execute("SELECT * FROM booking_client")
            legacy_clients = cursor.fetchall()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading legacy table: {e}"))
            return

        self.stdout.write(f"Found {len(legacy_clients)} legacy clients.")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for row in legacy_clients:
            phone = row["phone"] or None
            email = row["email"] or None

            # Robust lookup: try to find by phone OR email
            client = None
            if phone:
                client = Client.objects.filter(phone=phone).first()
            if not client and email:
                client = Client.objects.filter(email=email).first()

            if client:
                action = "Updating"
            else:
                action = "Creating"
                client = Client()

            # Mapping fields
            client.phone = phone
            client.email = email
            client.first_name = row["first_name"] or ""
            client.last_name = row["last_name"] or ""
            client.note = row.get("notes") or row.get("note") or ""
            client.status = row.get("status") or "guest"
            if hasattr(client, "instagram"):
                client.instagram = row.get("instagram") or ""
            if hasattr(client, "telegram"):
                client.telegram = row.get("telegram") or ""
            client.consent_marketing = bool(row.get("consent_marketing", False))
            consent_date_val = row.get("consent_date")
            if consent_date_val and hasattr(consent_date_val, "tzinfo"):
                client.consent_date = consent_date_val if consent_date_val.tzinfo else make_aware(consent_date_val)

            if row.get("access_token"):
                client.access_token = row["access_token"]

            client.is_ghost = row.get("user_id") is None and client.status == "guest"

            if not options["dry_run"]:
                try:
                    with transaction.atomic():
                        # Try to link User if not set
                        if not client.user_id:
                            user = None
                            if email:
                                user = User.objects.filter(email__iexact=email).first()
                            if not user and phone:
                                from system.models import UserProfile

                                profile = UserProfile.objects.filter(phone=phone).first()
                                if profile:
                                    user = profile.user

                            if user:
                                self.stdout.write(f"    Link user found: {user.username}")
                                client.user = user

                        client.save()

                        # Ensure verified EmailAddress for Allauth if user exists
                        if client.user and client.email:
                            EmailAddress.objects.get_or_create(
                                user=client.user,
                                email=client.email,
                                defaults={"verified": True, "primary": True},
                            )

                    if action == "Creating":
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error saving {client.first_name} {client.last_name}: {e}"))
                    skipped_count += 1
                    continue
            else:
                if action == "Creating":
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(f"  {action} client: {client.first_name} {client.last_name}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run - no changes saved."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration complete. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )

        conn.close()
