import os
from typing import Any

import psycopg2
from django.core.management.base import BaseCommand
from django.db import transaction
from features.booking.models import Master
from features.main.models import Service, ServiceCategory
from psycopg2.extras import RealDictCursor


class Command(BaseCommand):
    help = "Migrate services from legacy PostgreSQL database"

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, help="PostgreSQL connection URL")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes")

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
            # Fetch all services
            cursor.execute("SELECT * FROM main_service")
            legacy_services = cursor.fetchall()

            # Fetch master-category relationships
            cursor.execute("SELECT * FROM booking_master_categories")
            legacy_master_cats = cursor.fetchall()

            # Group masters by category
            category_masters_map: dict[Any, list[Any]] = {}
            for rel in legacy_master_cats:
                cat_id = rel["category_id"]
                m_id = rel["master_id"]
                if cat_id not in category_masters_map:
                    category_masters_map[cat_id] = []
                category_masters_map[cat_id].append(m_id)

            # Map legacy master IDs to new Master slugs/objects
            cursor.execute("SELECT id, slug FROM booking_master")
            master_id_to_slug = {row["id"]: row["slug"] for row in cursor.fetchall()}

            # Map legacy category IDs to new Category slugs
            cursor.execute("SELECT id, slug FROM main_category")
            category_id_to_slug = {row["id"]: row["slug"] for row in cursor.fetchall()}

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading legacy tables: {e}"))
            conn.close()
            return

        self.stdout.write(f"Found {len(legacy_services)} legacy services.")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for row in legacy_services:
            slug = row["slug"]

            service = Service.objects.filter(slug=slug).first()
            if service:
                action = "Updating"
            else:
                action = "Creating"
                service = Service(slug=slug)

            # Lookup category
            legacy_cat_id = row["category_id"]
            cat_slug = category_id_to_slug.get(legacy_cat_id)
            category = ServiceCategory.objects.filter(slug=cat_slug).first() if cat_slug else None

            if not category:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Skipping {row.get('title') or row.get('name', '')} (category {legacy_cat_id} not found)"
                    )
                )
                skipped_count += 1
                continue

            # Mapping fields
            service.category = category

            # Use base name if provided, else fallback to technical identifiers
            base_name = row.get("title") or row.get("name") or row.get("slug")
            service.name = base_name

            # Map translations if they exist in legacy
            for lang in ["de", "ru", "uk"]:
                # Try name/title translations
                translated_name = row.get(f"name_{lang}") or row.get(f"title_{lang}")
                if translated_name:
                    setattr(service, f"name_{lang}", translated_name)
                elif lang == "de" and not service.name_de:
                    # Fallback for DE to base name to avoid dimmed admin if no translation available
                    service.name_de = base_name

            # Mapping localized fields
            langs = ["en", "de", "ru", "uk"]

            # Map name, description, and content for each language
            for lang in langs:
                suffix = f"_{lang}" if lang != "en" else ""

                # Basic content
                setattr(service, f"name{suffix}", row.get(f"name{suffix}") or row.get(f"title{suffix}", ""))
                setattr(service, f"description{suffix}", row.get(f"description{suffix}", ""))
                setattr(service, f"content{suffix}", row.get(f"content{suffix}", ""))

                # SEO Metadata
                # Note: legacy might have 'seo_title' or 'meta_title'
                legacy_seo_title = row.get(f"seo_title{suffix}") or row.get(f"meta_title{suffix}")
                legacy_seo_desc = row.get(f"seo_description{suffix}") or row.get(f"meta_description{suffix}")

                if legacy_seo_title:
                    setattr(service, f"seo_title{suffix}", legacy_seo_title)
                if legacy_seo_desc:
                    setattr(service, f"seo_description{suffix}", legacy_seo_desc)

            service.price = row.get("price", 0)
            service.price_info = row.get("price_info", "")
            service.duration = row.get("duration")
            service.duration_info = row.get("duration_info", "")
            service.is_active = bool(row.get("is_active", True))
            service.is_hit = bool(row.get("is_hit", False))
            service.is_addon = bool(row.get("is_addon", False))
            service.order = row.get("order", 0)

            if row.get("image"):
                service.image = row["image"]

            if row.get("seo_image"):
                service.seo_image = row["seo_image"]

            if not options["dry_run"]:
                try:
                    with transaction.atomic():
                        service.save()

                        # Handle masters via category relationship
                        master_ids = category_masters_map.get(legacy_cat_id, [])
                        masters_to_add = []
                        for m_id in master_ids:
                            m_slug = master_id_to_slug.get(m_id)
                            m_obj = Master.objects.filter(slug=m_slug).first() if m_slug else None
                            if m_obj:
                                masters_to_add.append(m_obj)

                        if masters_to_add:
                            service.masters.set(masters_to_add)

                    if action == "Creating":
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error saving {service.name}: {e}"))
                    skipped_count += 1
                    continue
            else:
                if action == "Creating":
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(f"  {action} service: {service.name}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run - no changes saved."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration complete. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )

        conn.close()
