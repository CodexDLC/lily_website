from core.logger import log
from django.conf import settings
from django.core.cache import cache
from features.system.fixtures.content.static_translations import DATA
from features.system.management.commands.base_hash_command import HashProtectedCommand
from features.system.models.static_translation import StaticTranslation

LANGUAGES = ("de", "ru", "uk", "en")


class Command(HashProtectedCommand):
    help = "Update or create static translations in the database from fixtures file"
    fixture_key = "update_static_translations"

    def get_fixture_paths(self) -> list:
        path = settings.BASE_DIR / "features" / "system" / "fixtures" / "content" / "static_translations.py"
        return [path]

    def handle_import(self, *args, **options):
        log.info("Command: update_static_translations | Action: Start")

        count_created = 0
        count_updated = 0
        count_skipped = 0
        has_any_changes = False

        log.debug(f"Command: update_static_translations | Action: ProcessingKeys | count={len(DATA)}")

        for key, translations in DATA.items():
            obj, created = StaticTranslation.objects.get_or_create(key=key)

            if created:
                for lang, text in translations.items():
                    field_name = f"text_{lang}"
                    if hasattr(obj, field_name):
                        setattr(obj, field_name, text)
                obj.save()
                count_created += 1
                has_any_changes = True
                log.debug(f"Command: update_static_translations | Action: Created | key={key}")
            else:
                changed_fields = []
                for lang, text in translations.items():
                    field_name = f"text_{lang}"
                    if hasattr(obj, field_name):
                        current = getattr(obj, field_name)
                        if current != text:
                            setattr(obj, field_name, text)
                            changed_fields.append(field_name)

                if changed_fields:
                    obj.save()
                    count_updated += 1
                    has_any_changes = True
                    log.debug(
                        f"Command: update_static_translations | Action: Updated | key={key} | fields={changed_fields}"
                    )
                else:
                    count_skipped += 1

        if has_any_changes:
            keys_to_delete = [f"static_content_{lang}" for lang in LANGUAGES]
            cache.delete_many(keys_to_delete)
            log.info(f"Command: update_static_translations | Action: CacheInvalidated | keys={keys_to_delete}")
            self.stdout.write(self.style.SUCCESS("  Cache invalidated for static_content_* keys."))

        log.info(
            f"Command: update_static_translations | Action: Success | created={count_created} | updated={count_updated} | skipped={count_skipped}"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {len(DATA)} keys. "
                f"Created: {count_created}, Updated: {count_updated}, Skipped: {count_skipped}"
            )
        )
