import json

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from features.main.models import Service


class Command(BaseCommand):
    help = "Smart update SEO fields for Services from JSON fixtures (Bulk Update)"

    def handle(self, *args, **options):
        fixtures_dir = settings.BASE_DIR / "features" / "system" / "fixtures" / "seo"

        if not fixtures_dir.exists():
            self.stdout.write(self.style.ERROR(f"Directory not found: {fixtures_dir}"))
            return

        json_files = list(fixtures_dir.glob("*.json"))
        if not json_files:
            self.stdout.write(self.style.WARNING(f"No JSON files found in {fixtures_dir}"))
            return

        # 1. Collect all data from all files
        all_seo_data = {}
        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    all_seo_data.update(data)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"Error decoding {json_file.name}: {e}"))

        if not all_seo_data:
            self.stdout.write("No data to process.")
            return

        # 2. Fetch all relevant services in one query
        slugs = list(all_seo_data.keys())
        services = Service.objects.filter(slug__in=slugs)
        services_map = {s.slug: s for s in services}

        services_to_update = []
        updated_fields_set = set()
        cache_keys_to_delete = []

        not_found_count = 0
        skipped_count = 0

        # 3. Compare and prepare updates
        for slug, new_data in all_seo_data.items():
            service = services_map.get(slug)

            if not service:
                self.stdout.write(self.style.ERROR(f"  [404] {slug} (Not found in DB)"))
                not_found_count += 1
                continue

            has_changes = False
            for field, new_value in new_data.items():
                if hasattr(service, field):
                    current_value = getattr(service, field)
                    # Simple comparison (handles strings well)
                    if current_value != new_value:
                        setattr(service, field, new_value)
                        updated_fields_set.add(field)
                        has_changes = True

            if has_changes:
                services_to_update.append(service)
                # Collect cache keys for invalidation
                cache_keys_to_delete.extend(
                    [f"service_detail_{service.slug}", f"category_detail_{service.category.slug}"]
                )
                self.stdout.write(self.style.SUCCESS(f"  [UPDATE] {slug}"))
            else:
                skipped_count += 1
                # self.stdout.write(f"  [SKIP] {slug} (No changes)") # Uncomment for verbose

        # 4. Bulk Update
        if services_to_update:
            # Always update 'updated_at' if your model uses it, but bulk_update doesn't touch auto_now fields automatically
            # unless we explicitly include them. But usually we just update the changed fields.

            Service.objects.bulk_update(services_to_update, fields=list(updated_fields_set))

            # 5. Invalidate Cache
            if cache_keys_to_delete:
                # Add global keys
                cache_keys_to_delete.extend(["active_services_cache", "popular_services_cache"])
                try:
                    cache.delete_many(list(set(cache_keys_to_delete)))  # Unique keys
                    self.stdout.write(self.style.SUCCESS("Cache invalidated."))
                except Exception:
                    self.stdout.write(self.style.WARNING("Cache invalidation failed (Redis down?)"))

            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully updated {len(services_to_update)} services."))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo changes needed. All SEO data is up to date."))

        self.stdout.write(
            f"Stats: {len(services_to_update)} updated, {skipped_count} skipped, {not_found_count} not found."
        )
