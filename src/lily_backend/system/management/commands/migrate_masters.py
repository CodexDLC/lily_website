import json
import os
import sqlite3
from datetime import time

import psycopg2
from django.core.management.base import BaseCommand
from django.db import transaction
from features.booking.booking_settings import BookingSettings
from features.booking.models import Master, MasterWorkingDay
from features.main.models import ServiceCategory
from psycopg2.extras import RealDictCursor

from system.models import Client


class Command(BaseCommand):
    help = "Migrate masters from legacy sqlite or postgres database"

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
            cursor.execute("SELECT * FROM booking_master")
            legacy_masters = cursor.fetchall()
            cursor.execute("SELECT * FROM booking_master_categories")
            legacy_master_categories = cursor.fetchall()
            cursor.execute("SELECT id, slug FROM main_category")
            legacy_categories = cursor.fetchall()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading legacy table: {e}"))
            return

        self.stdout.write(f"Found {len(legacy_masters)} legacy masters.")

        category_id_to_slug = {self._row_get(row, "id"): self._row_get(row, "slug") for row in legacy_categories}
        master_category_ids: dict[object, list[object]] = {}
        for rel in legacy_master_categories:
            master_category_ids.setdefault(self._row_get(rel, "master_id"), []).append(
                self._row_get(rel, "category_id")
            )

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for row in legacy_masters:
            slug = self._row_get(row, "slug")
            legacy_master_id = self._row_get(row, "id")

            master = Master.objects.filter(slug=slug).first()
            if master:
                action = "Updating"
            else:
                action = "Creating"
                master = Master(slug=slug)

            # Mapping localized fields
            langs = ["en", "de", "ru", "uk"]

            # Map name, title, bio, and short_description for each language
            for lang in langs:
                suffix = f"_{lang}" if lang != "en" else ""

                # Basic content
                setattr(master, f"title{suffix}", self._row_get(row, f"title{suffix}") or "")
                setattr(master, f"bio{suffix}", self._row_get(row, f"bio{suffix}") or "")
                setattr(master, f"short_description{suffix}", self._row_get(row, f"short_description{suffix}") or "")

                # SEO Metadata
                legacy_seo_title = self._row_get(row, f"seo_title{suffix}") or self._row_get(row, f"meta_title{suffix}")
                legacy_seo_desc = self._row_get(row, f"seo_description{suffix}") or self._row_get(
                    row, f"meta_description{suffix}"
                )

                if legacy_seo_title:
                    setattr(master, f"seo_title{suffix}", legacy_seo_title)
                if legacy_seo_desc:
                    setattr(master, f"seo_description{suffix}", legacy_seo_desc)

            master.name = self._row_get(row, "name")
            # Don't try to migrate the photo file itself, just the path string
            master.photo = self._row_get(row, "photo")

            if self._row_get(row, "seo_image"):
                master.seo_image = self._row_get(row, "seo_image")
            master.years_experience = self._row_get(row, "years_experience", 0)
            master.instagram = self._row_get(row, "instagram") or ""
            master.phone = self._row_get(row, "phone") or ""
            master.status = self._normalize_status(self._row_get(row, "status") or "active")
            master.is_owner = bool(self._row_get(row, "is_owner"))
            master.is_featured = bool(self._row_get(row, "is_featured"))
            master.is_public = bool(self._row_get(row, "is_public"))
            master.order = self._row_get(row, "order", 0)
            master.work_start = self._parse_time(self._row_get(row, "work_start"))
            master.work_end = self._parse_time(self._row_get(row, "work_end"))
            master.break_start = self._parse_time(self._row_get(row, "break_start"))
            master.break_end = self._parse_time(self._row_get(row, "break_end"))

            # Telegram fields
            master.telegram_id = self._row_get(row, "telegram_id")
            master.telegram_username = self._row_get(row, "telegram_username") or ""
            if self._row_get(row, "bot_access_code"):
                master.bot_access_code = self._row_get(row, "bot_access_code")
            if self._row_get(row, "qr_token"):
                master.qr_token = self._row_get(row, "qr_token")

            # Try to link User if not set
            if not master.user_id and master.phone:
                client_with_user = Client.objects.filter(phone=master.phone, user__isnull=False).first()
                if client_with_user:
                    master.user = client_with_user.user

            if not options["dry_run"]:
                try:
                    with transaction.atomic():
                        master.save()
                        self._sync_master_categories(
                            master=master,
                            legacy_category_ids=master_category_ids.get(legacy_master_id, []),
                            category_id_to_slug=category_id_to_slug,
                        )
                        self._sync_working_days(master=master, raw_work_days=self._row_get(row, "work_days"))
                    if action == "Creating":
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error saving {master.name}: {e}"))
                    skipped_count += 1
                    continue
            else:
                if action == "Creating":
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(f"  {action} master: {master.name}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run - no changes saved."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration complete. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )

        conn.close()

    @staticmethod
    def _row_get(row, key, default=None):
        if hasattr(row, "get"):
            return row.get(key, default)
        try:
            return row[key]
        except Exception:
            return default

    @staticmethod
    def _normalize_status(value: str) -> str:
        return "inactive" if value == "fired" else value

    @staticmethod
    def _parse_time(value) -> time | None:
        if not value:
            return None
        if isinstance(value, time):
            return value
        text = str(value).strip()
        if not text:
            return None
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                from datetime import datetime

                return datetime.strptime(text, fmt).time()
            except ValueError:
                continue
        return None

    def _sync_master_categories(
        self, *, master: Master, legacy_category_ids: list[object], category_id_to_slug: dict
    ) -> None:
        slugs = [category_id_to_slug.get(cat_id) for cat_id in legacy_category_ids]
        categories = list(ServiceCategory.objects.filter(slug__in=[slug for slug in slugs if slug]))
        master.categories.set(categories)

    def _sync_working_days(self, *, master: Master, raw_work_days) -> None:
        parsed_days = self._parse_work_days(raw_work_days)
        master.working_days.all().delete()
        if not parsed_days:
            return

        booking_settings = BookingSettings.load()
        for weekday in parsed_days:
            booking_day_schedule = booking_settings.get_day_schedule(weekday)
            fallback_start = booking_day_schedule[0] if booking_day_schedule is not None else None
            fallback_end = booking_day_schedule[1] if booking_day_schedule is not None else None
            start_time = master.work_start or fallback_start
            end_time = master.work_end or fallback_end
            if not start_time or not end_time:
                continue
            MasterWorkingDay.objects.update_or_create(
                master=master,
                weekday=weekday,
                defaults={
                    "start_time": start_time,
                    "end_time": end_time,
                    "break_start": master.break_start,
                    "break_end": master.break_end,
                },
            )

    @staticmethod
    def _parse_work_days(raw_value) -> list[int]:
        if raw_value in (None, "", []):
            return []
        value = raw_value
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return []
        if not isinstance(value, list):
            return []
        days: list[int] = []
        for item in value:
            try:
                day = int(item)
            except (TypeError, ValueError):
                continue
            if 0 <= day <= 6 and day not in days:
                days.append(day)
        return sorted(days)
