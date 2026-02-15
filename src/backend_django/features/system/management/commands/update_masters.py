import json

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from features.booking.models import Master


class Command(BaseCommand):
    help = "Update content fields for Masters from JSON fixtures (Bulk Update)"

    def handle(self, *args, **options):
        fixtures_dir = settings.BASE_DIR / "features" / "system" / "fixtures" / "content"

        if not fixtures_dir.exists():
            self.stdout.write(self.style.ERROR(f"Directory not found: {fixtures_dir}"))
            return

        json_files = list(fixtures_dir.glob("*.json"))
        if not json_files:
            self.stdout.write(self.style.WARNING(f"No JSON files found in {fixtures_dir}"))
            return

        # 1. Collect all data
        all_data = {}
        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    all_data.update(data)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"Error decoding {json_file.name}: {e}"))

        if not all_data:
            self.stdout.write("No data to process.")
            return

        # 2. Fetch masters
        slugs = list(all_data.keys())
        masters = Master.objects.filter(slug__in=slugs)
        masters_map = {m.slug: m for m in masters}

        masters_to_update = []
        updated_fields_set = set()
        cache_keys_to_delete = []

        not_found_count = 0
        skipped_count = 0

        # 3. Compare
        for slug, new_data in all_data.items():
            master = masters_map.get(slug)

            if not master:
                self.stdout.write(self.style.ERROR(f"  [404] {slug} (Not found in DB)"))
                not_found_count += 1
                continue

            has_changes = False
            for field, new_value in new_data.items():
                if hasattr(master, field):
                    current_value = getattr(master, field)
                    if current_value != new_value:
                        setattr(master, field, new_value)
                        updated_fields_set.add(field)
                        has_changes = True

            if has_changes:
                masters_to_update.append(master)
                cache_keys_to_delete.extend(["active_masters_cache", "salon_owner_cache", "team_members_cache"])
                self.stdout.write(self.style.SUCCESS(f"  [UPDATE] {slug}"))
            else:
                skipped_count += 1

        # 4. Bulk Update
        if masters_to_update:
            Master.objects.bulk_update(masters_to_update, fields=list(updated_fields_set))

            if cache_keys_to_delete:
                try:
                    cache.delete_many(list(set(cache_keys_to_delete)))
                    self.stdout.write(self.style.SUCCESS("Cache invalidated."))
                except Exception:
                    pass

            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully updated {len(masters_to_update)} masters."))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo changes needed."))

        self.stdout.write(
            f"Stats: {len(masters_to_update)} updated, {skipped_count} skipped, {not_found_count} not found."
        )
