import json

from core.logger import log
from django.conf import settings
from django.core.cache import cache
from features.booking.models import Master
from features.system.management.commands.base_hash_command import HashProtectedCommand


class Command(HashProtectedCommand):
    help = "Update content fields for Masters from JSON fixtures (Bulk Update)"
    fixture_key = "update_masters"

    def get_fixture_paths(self) -> list:
        fixtures_dir = settings.BASE_DIR / "features" / "system" / "fixtures" / "content"
        if not fixtures_dir.exists():
            return []
        return [fixtures_dir / "masters.json"]

    def handle_import(self, *args, **options):
        log.info("Command: update_masters | Action: Start")

        fixtures_dir = settings.BASE_DIR / "features" / "system" / "fixtures" / "content"
        log.debug(f"Command: update_masters | Action: LoadFixtures | path={fixtures_dir}")

        if not fixtures_dir.exists():
            log.error(f"Command: update_masters | Action: Failed | error=Directory not found | path={fixtures_dir}")
            self.stdout.write(self.style.ERROR(f"Directory not found: {fixtures_dir}"))
            return

        json_files = list(fixtures_dir.glob("*.json"))
        if not json_files:
            log.warning(f"Command: update_masters | Action: NoFixturesFound | path={fixtures_dir}")
            self.stdout.write(self.style.WARNING(f"No JSON files found in {fixtures_dir}"))
            return

        # 1. Collect all data
        all_data = {}
        for json_file in json_files:
            # Skip site_settings.json (it has different format)
            if json_file.name == "site_settings.json":
                continue

            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    # Only process if data is a dict (masters format)
                    if isinstance(data, dict):
                        all_data.update(data)
                        log.debug(
                            f"Command: update_masters | Action: ReadFile | file={json_file.name} | keys={len(data)}"
                        )
            except json.JSONDecodeError as e:
                log.error(f"Command: update_masters | Action: JSONError | file={json_file.name} | error={e}")
                self.stdout.write(self.style.ERROR(f"Error decoding {json_file.name}: {e}"))

        if not all_data:
            log.info("Command: update_masters | Action: NoDataToProcess")
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
                log.warning(f"Command: update_masters | Action: SkipMaster | slug={slug} | reason=NotFoundInDB")
                self.stdout.write(self.style.ERROR(f"  [404] {slug} (Not found in DB)"))
                not_found_count += 1
                continue

            has_changes = False
            changed_fields = []
            for field, new_value in new_data.items():
                if hasattr(master, field):
                    current_value = getattr(master, field)
                    if current_value != new_value:
                        setattr(master, field, new_value)
                        updated_fields_set.add(field)
                        has_changes = True
                        changed_fields.append(field)

            if has_changes:
                masters_to_update.append(master)
                cache_keys_to_delete.extend(["active_masters_cache", "salon_owner_cache", "team_members_cache"])
                log.info(f"Command: update_masters | Action: Updated | slug={slug} | fields={changed_fields}")
                self.stdout.write(self.style.SUCCESS(f"  [UPDATE] {slug}"))
            else:
                skipped_count += 1

        # 4. Bulk Update
        if masters_to_update:
            Master.objects.bulk_update(masters_to_update, fields=list(updated_fields_set))
            log.info(
                f"Command: update_masters | Action: BulkUpdate | count={len(masters_to_update)} | fields={list(updated_fields_set)}"
            )

            if cache_keys_to_delete:
                try:
                    cache.delete_many(list(set(cache_keys_to_delete)))
                    log.info(
                        f"Command: update_masters | Action: CacheInvalidated | keys={list(set(cache_keys_to_delete))}"
                    )
                    self.stdout.write(self.style.SUCCESS("Cache invalidated."))
                except Exception as e:
                    log.error(f"Command: update_masters | Action: CacheError | error={e}")

            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully updated {len(masters_to_update)} masters."))
        else:
            log.info("Command: update_masters | Action: NoChanges")
            self.stdout.write(self.style.SUCCESS("\nNo changes needed."))

        log.info(
            f"Command: update_masters | Action: Success | updated={len(masters_to_update)} | skipped={skipped_count} | not_found={not_found_count}"
        )
