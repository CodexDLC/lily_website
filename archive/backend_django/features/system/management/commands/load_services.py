import json

from core.logger import log
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import OperationalError, transaction
from features.system.management.commands.base_hash_command import HashProtectedCommand


class Command(HashProtectedCommand):
    help = "Load services from JSON fixtures in features/system/fixtures/content/service"
    fixture_key = "load_services"

    def add_arguments(self, parser):
        super().add_arguments(parser)
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

    def get_fixture_paths(self) -> list:
        fixtures_dir = settings.BASE_DIR / "features" / "system" / "fixtures" / "content" / "service"
        if not fixtures_dir.exists():
            return []
        return list(fixtures_dir.glob("*.json"))

    def handle_import(self, *args, **options):
        clean = options.get("clean", False)
        dry_run = options.get("dry_run", False)
        log.info(f"Command: load_services | Action: Start | clean={clean} | dry_run={dry_run}")

        # 1. Path Configuration
        fixtures_dir = settings.BASE_DIR / "features" / "system" / "fixtures" / "content" / "service"

        if not fixtures_dir.exists():
            log.error(f"Command: load_services | Action: Failed | error=Directory not found | path={fixtures_dir}")
            self.stdout.write(self.style.ERROR(f"Directory not found: {fixtures_dir}"))
            return

        json_files = list(fixtures_dir.glob("*.json"))
        if not json_files:
            log.warning(f"Command: load_services | Action: NoFixturesFound | path={fixtures_dir}")
            self.stdout.write(self.style.WARNING(f"No JSON files found in {fixtures_dir}"))
            return

        Service = apps.get_model("main", "Service")

        updated_count = 0
        created_count = 0
        skipped_count = 0
        processed_pks = set()
        affected_category_ids = set()

        log.debug(f"Command: load_services | Action: ProcessingFiles | count={len(json_files)}")

        try:
            with transaction.atomic():
                # 2. Iterate and compare
                for json_file in json_files:
                    log.debug(f"Command: load_services | Action: ReadFile | file={json_file.name}")

                    try:
                        with open(json_file, encoding="utf-8") as f:
                            data = json.load(f)

                        if not isinstance(data, list):
                            log.warning(
                                f"Command: load_services | Action: SkipFile | file={json_file.name} | reason=NotAList"
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

                            if dry_run:
                                log.debug(
                                    f"Command: load_services | Action: DryRun | pk={pk} | title={fields.get('title')}"
                                )
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
                                    log.info(
                                        f"Command: load_services | Action: Updated | pk={pk} | title={existing.title}"
                                    )
                                else:
                                    skipped_count += 1

                            except Service.DoesNotExist:
                                Service.objects.create(pk=pk, **final_defaults)
                                created_count += 1
                                affected_category_ids.add(final_defaults.get("category_id"))
                                log.info(
                                    f"Command: load_services | Action: Created | pk={pk} | title={fields.get('title')}"
                                )

                    except json.JSONDecodeError as e:
                        log.error(f"Command: load_services | Action: JSONError | file={json_file.name} | error={e}")

                # 3. Clean up (Optional)
                if clean and not dry_run:
                    all_pks = set(Service.objects.values_list("pk", flat=True))
                    to_delete = all_pks - processed_pks

                    if to_delete:
                        deleted_cat_ids = set(
                            Service.objects.filter(pk__in=to_delete).values_list("category_id", flat=True)
                        )
                        affected_category_ids.update(deleted_cat_ids)
                        count = Service.objects.filter(pk__in=to_delete).delete()[0]
                        log.warning(f"Command: load_services | Action: CleanUp | deleted_count={count}")
                    else:
                        log.debug("Command: load_services | Action: CleanUp | status=NoExtraneous")

        except Exception as e:
            log.error(f"Command: load_services | Action: Failed | error={e}")
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            return

        if dry_run:
            log.info("Command: load_services | Action: DryRunComplete")
            return

        # 4. Invalidate only affected cache keys
        if affected_category_ids or created_count or updated_count:
            try:
                from features.main.models import Category

                affected_slugs = list(
                    Category.objects.filter(pk__in=affected_category_ids).values_list("slug", flat=True)
                )
                keys_to_delete = [
                    "home_bento_cache_v5",
                    "bento_groups_cache",
                    "price_list_cache_all",
                ]
                for slug in affected_slugs:
                    keys_to_delete.append(f"category_detail_cache_{slug}")
                    keys_to_delete.append(f"price_list_cache_{slug}")

                cache.delete_many(keys_to_delete)
                log.info(f"Command: load_services | Action: CacheInvalidated | keys_count={len(keys_to_delete)}")
            except (OperationalError, Exception) as e:
                log.error(f"Command: load_services | Action: CacheInvalidationFailed | error={e}")

        log.info(
            f"Command: load_services | Action: Success | created={created_count} | updated={updated_count} | skipped={skipped_count}"
        )
