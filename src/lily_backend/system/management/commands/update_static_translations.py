from codex_django.system.management import JsonFixtureUpsertCommand
from django.conf import settings


class Command(JsonFixtureUpsertCommand):
    help = "Update Static Translations from JSON fixture (system/fixtures/content/static_translations.json)"
    fixture_key = "static_translations"
    fixture_path = settings.BASE_DIR / "system" / "fixtures" / "content" / "static_translations.json"
    model_path = "system.StaticTranslation"
    lookup_field = "key"
