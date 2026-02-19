import json

from django.apps import apps
from django.conf import settings
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
        # User specified path: src\backend_django\features\system\fixtures\content\service
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
        processed_pks = set()

        self.stdout.write(f"Found {len(json_files)} fixture files.")

        try:
            with transaction.atomic():
                # 2. Iterate and Upsert
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
                            # because 'category' expects a model instance, but we provide an ID.
                            final_defaults = {}
                            for key, value in fields.items():
                                if key == "category":
                                    final_defaults["category_id"] = value
                                else:
                                    final_defaults[key] = value

                            obj, created = Service.objects.update_or_create(pk=pk, defaults=final_defaults)

                            if created:
                                created_count += 1
                                self.stdout.write(self.style.SUCCESS(f"  [CREATED] PK {pk}: {obj.title}"))
                            else:
                                updated_count += 1
                                # self.stdout.write(f"  [UPDATED] PK {pk}: {obj.title}") # Verbose

                    except json.JSONDecodeError:
                        self.stdout.write(self.style.ERROR(f"  Error decoding JSON in {json_file.name}"))

                # 3. Clean up (Optional)
                if options["clean"] and not options["dry_run"]:
                    all_pks = set(Service.objects.values_list("pk", flat=True))
                    to_delete = all_pks - processed_pks

                    if to_delete:
                        count = Service.objects.filter(pk__in=to_delete).delete()[0]
                        self.stdout.write(
                            self.style.WARNING(f"\n[CLEAN] Deleted {count} services not present in fixtures.")
                        )
                    else:
                        self.stdout.write(self.style.SUCCESS("\n[CLEAN] No extraneous services found."))

                # Raise exception if dry run to rollback transaction (just in case, though we didn't write)
                # Actually standard practice for dry-run is just not calling save(), but here we use logic.
                # Since we didn't call update_or_create in dry_run, no DB hits.

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            return

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("\nDry run complete. No changes made."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nDone! Created: {created_count}, Updated: {updated_count}"))
