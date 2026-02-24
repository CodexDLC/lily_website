import json

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Load services from JSON fixtures in features/system/fixtures/content/service"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete services that are NOT in the fixtures (WARNING: Destructive)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would happen without making changes",
        )

    def handle(self, *args, **options):
        # 1. Path Configuration
        fixtures_dir = settings.BASE_DIR / "features" / "system" / "fixtures" / "content" / "service"

        if not fixtures_dir.exists():
            self.stdout.write(self.style.ERROR(f"Directory not found: {fixtures_dir}"))
            self.stdout.write(
                self.style.WARNING("Please ensure you created the 'service' subdirectory and moved JSONs there.")
            )
            return

        json_files = list(fixtures_dir.glob("*.json"))
        if not json_files:
            self.stdout.write(self.style.WARNING(f"No JSON files found in {fixtures_dir}"))
            return

        Service = apps.get_model("main", "Service")

        updated_count = 0
        created_count = 0
        skipped_count = 0
        processed_pks = set()
        affected_category_ids = set()

        self.stdout.write(f"Found {len(json_files)} fixture files.")

        try:
            with transaction.atomic():
                # 2. Iterate and compare
                for json_file in json_files:
                    self.stdout.write(f"Processing {json_file.name}...")

                    try:
                        with open(json_file, encoding="utf-8") as f:
                            data = json.load(f)

                        if not isinstance(data, list):
                            self.stdout.write(
                                self.style.WARNING(f"  Skipping {json_file.name}: Expected list, got {type(data)}")
                            )
                            continue

                        for item in data:
                            if item.get("model") != "main.service":
                                continue

                            pk = item.get("pk")
                            fields = item.get("fields", {})

                            if not pk:
                                continue

                            processed_pks.add(pk)

                            if options["dry_run"]:
                                self.stdout.write(f"  [DRY-RUN] would process PK {pk}: {fields.get('title')}")
                                continue

                            # Fix for ForeignKey: rename 'category' to 'category_id'
                            final_defaults = {}
                            for key, value in fields.items():
                                if key == "category":
                                    final_defaults["category_id"] = value
                                else:
                                    final_defaults[key] = value

                            # Check if exists and compare
                            try:
                                existing = Service.objects.get(pk=pk)
                                has_changes = False
                                for field, new_value in final_defaults.items():
                                    current_value = getattr(existing, field, None)
                                    if str(current_value) != str(new_value):
                                        has_changes = True
                                        break

                                if has_changes:
                                    for field, value in final_defaults.items():
                                        setattr(existing, field, value)
                                    existing.save()
                                    updated_count += 1
                                    affected_category_ids.add(existing.category_id)
                                    self.stdout.write(self.style.SUCCESS(f"  [UPDATED] PK {pk}: {existing.title}"))
                                else:
                                    skipped_count += 1

                            except Service.DoesNotExist:
                                Service.objects.create(pk=pk, **final_defaults)
                                created_count += 1
                                affected_category_ids.add(final_defaults.get("category_id"))
                                self.stdout.write(self.style.SUCCESS(f"  [CREATED] PK {pk}: {fields.get('title')}"))

                    except json.JSONDecodeError:
                        self.stdout.write(self.style.ERROR(f"  Error decoding JSON in {json_file.name}"))

                # 3. Clean up (Optional)
                if options["clean"] and not options["dry_run"]:
                    all_pks = set(Service.objects.values_list("pk", flat=True))
                    to_delete = all_pks - processed_pks

                    if to_delete:
                        # Collect category IDs before deleting
                        deleted_cat_ids = set(
                            Service.objects.filter(pk__in=to_delete).values_list("category_id", flat=True)
                        )
                        affected_category_ids.update(deleted_cat_ids)
                        count = Service.objects.filter(pk__in=to_delete).delete()[0]
                        self.stdout.write(
                            self.style.WARNING(f"\n[CLEAN] Deleted {count} services not present in fixtures.")
                        )
                    else:
                        self.stdout.write(self.style.SUCCESS("\n[CLEAN] No extraneous services found."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            return

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("\nDry run complete. No changes made."))
            return

        # 4. Invalidate only affected cache keys
        if affected_category_ids or created_count or updated_count:
            from features.main.models import Category

            affected_slugs = list(Category.objects.filter(pk__in=affected_category_ids).values_list("slug", flat=True))
            keys_to_delete = [
                "home_bento_cache_v5",
                "bento_groups_cache",
                "price_list_cache_all",
            ]
            for slug in affected_slugs:
                keys_to_delete.append(f"category_detail_cache_{slug}")
                keys_to_delete.append(f"price_list_cache_{slug}")
            cache.delete_many(keys_to_delete)
            self.stdout.write(self.style.SUCCESS(f"  Cache invalidated for {len(keys_to_delete)} keys."))

        self.stdout.write(
            self.style.SUCCESS(f"\nDone! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}")
        )
