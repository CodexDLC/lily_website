import os
import sqlite3
from datetime import datetime
from typing import Any

import psycopg2
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from psycopg2.extras import RealDictCursor

from system.models import Client

User = get_user_model()


def _row_get(row: Any, key: str, default: Any = None) -> Any:
    if hasattr(row, "get"):
        return row.get(key, default)
    try:
        return row[key]
    except (IndexError, KeyError):
        return default


def _coerce_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, str):
        value = parse_datetime(value)
    if not isinstance(value, datetime):
        return None
    return timezone.make_aware(value) if timezone.is_naive(value) else value


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
            phone = _row_get(row, "phone") or None
            email = _row_get(row, "email") or None

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
            client.first_name = _row_get(row, "first_name") or ""
            client.last_name = _row_get(row, "last_name") or ""
            client.note = _row_get(row, "notes") or _row_get(row, "note") or ""
            client.status = _row_get(row, "status") or "guest"
            if hasattr(client, "instagram"):
                client.instagram = _row_get(row, "instagram") or ""
            if hasattr(client, "telegram"):
                client.telegram = _row_get(row, "telegram") or ""
            client.consent_marketing = bool(_row_get(row, "consent_marketing", False))
            consent_date_val = _coerce_datetime(_row_get(row, "consent_date"))
            if consent_date_val:
                client.consent_date = consent_date_val

            if _row_get(row, "access_token"):
                client.access_token = _row_get(row, "access_token")

            client.is_ghost = _row_get(row, "user_id") is None and client.status == "guest"
            legacy_created_at = _coerce_datetime(_row_get(row, "created_at"))
            legacy_updated_at = _coerce_datetime(_row_get(row, "updated_at")) or legacy_created_at

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
                        timestamp_updates = {}
                        if legacy_created_at:
                            timestamp_updates["created_at"] = legacy_created_at
                        if legacy_updated_at:
                            timestamp_updates["updated_at"] = legacy_updated_at
                        if timestamp_updates:
                            Client.objects.filter(pk=client.pk).update(**timestamp_updates)

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
