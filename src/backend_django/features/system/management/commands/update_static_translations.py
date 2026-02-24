from django.core.cache import cache
from django.core.management.base import BaseCommand
from features.system.fixtures.content.static_translations import DATA
from features.system.models.static_translation import StaticTranslation

LANGUAGES = ("de", "ru", "uk", "en")


class Command(BaseCommand):
    help = "Update or create static translations in the database from fixtures file"

    def handle(self, *args, **options):
        self.stdout.write("Updating Static Translations from fixtures...")

        count_created = 0
        count_updated = 0
        count_skipped = 0
        has_any_changes = False

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
                else:
                    count_skipped += 1

        if has_any_changes:
            keys_to_delete = [f"static_content_{lang}" for lang in LANGUAGES]
            cache.delete_many(keys_to_delete)
            self.stdout.write(self.style.SUCCESS("  Cache invalidated for static_content_* keys."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {len(DATA)} keys. "
                f"Created: {count_created}, Updated: {count_updated}, Skipped: {count_skipped}"
            )
        )
