import os

import psycopg2
from django.core.management.base import BaseCommand
from django.db import transaction
from features.main.models import ServiceCategory
from psycopg2.extras import RealDictCursor


class Command(BaseCommand):
    help = "Migrate service categories from legacy PostgreSQL database"

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, help="PostgreSQL connection URL")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes")
        parser.add_argument("--skip-images", action="store_true", help="Do not overwrite image/icon paths")
        parser.add_argument("--keep-status", action="store_true", help="Do not overwrite is_planned status")

    def handle(self, *args, **options):
        db_url = options["url"] or os.environ.get("LEGACY_DATABASE_URL")

        if not db_url:
            self.stdout.write(self.style.ERROR("Must provide --url (postgres) or set LEGACY_DATABASE_URL env var"))
            return

        self.stdout.write(f"Connecting to PostgreSQL: {db_url[:30]}...")
        try:
            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Connection failed: {e}"))
            return

        try:
            cursor.execute("SELECT * FROM main_category")
            legacy_categories = cursor.fetchall()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading legacy table: {e}"))
            conn.close()
            return

        self.stdout.write(f"Found {len(legacy_categories)} legacy categories.")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for row in legacy_categories:
            slug = row["slug"]

            category = ServiceCategory.objects.filter(slug=slug).first()
            if category:
                action = "Updating"
            else:
                action = "Creating"
                category = ServiceCategory(slug=slug)

            # Mapping localized fields
            langs = ["en", "de", "ru", "uk"]

            # Map name, description, and content for each language
            for lang in langs:
                suffix = f"_{lang}" if lang != "en" else ""

                # Basic content
                setattr(category, f"name{suffix}", row.get(f"name{suffix}") or row.get(f"title{suffix}", ""))
                setattr(category, f"description{suffix}", row.get(f"description{suffix}", ""))
                setattr(category, f"content{suffix}", row.get(f"content{suffix}", ""))

                # SEO Metadata
                legacy_seo_title = row.get(f"seo_title{suffix}") or row.get(f"meta_title{suffix}")
                legacy_seo_desc = row.get(f"seo_description{suffix}") or row.get(f"meta_description{suffix}")

                if legacy_seo_title:
                    setattr(category, f"seo_title{suffix}", legacy_seo_title)
                if legacy_seo_desc:
                    setattr(category, f"seo_description{suffix}", legacy_seo_desc)

            category.bento_group = row.get("bento_group", "")
            category.order = row.get("order", 0)

            if not options["keep_status"]:
                category.is_planned = bool(row.get("is_planned", False))

            # Note: image and icon paths are migrated as strings, assuming storage is shared or paths match
            if not options["skip_images"]:
                if row.get("image"):
                    category.image = row["image"]
                if row.get("icon"):
                    category.icon = row["icon"]

            if row.get("seo_image"):
                category.seo_image = row["seo_image"]

            if not options["dry_run"]:
                try:
                    with transaction.atomic():
                        category.save()
                    if action == "Creating":
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error saving {category.name}: {e}"))
                    skipped_count += 1
                    continue
            else:
                if action == "Creating":
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(f"  {action} category: {category.name}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run - no changes saved."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration complete. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )

        conn.close()
