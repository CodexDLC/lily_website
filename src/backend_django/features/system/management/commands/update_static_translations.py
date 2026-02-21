from django.core.management.base import BaseCommand
from features.system.fixtures.content.static_translations import DATA
from features.system.models.static_translation import StaticTranslation


class Command(BaseCommand):
    help = "Update or create static translations in the database from fixtures file"

    def handle(self, *args, **options):
        self.stdout.write("Updating Static Translations from fixtures...")

        count_created = 0
        count_updated = 0

        for key, translations in DATA.items():
            obj, created = StaticTranslation.objects.get_or_create(key=key)

            # Update each language field
            for lang, text in translations.items():
                field_name = f"text_{lang}"
                if hasattr(obj, field_name):
                    setattr(obj, field_name, text)

            obj.save()

            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {len(DATA)} keys. Created: {count_created}, Updated: {count_updated}"
            )
        )
