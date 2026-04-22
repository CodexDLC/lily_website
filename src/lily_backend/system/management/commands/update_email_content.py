from codex_django.system.management import JsonFixtureUpsertCommand
from django.conf import settings


class Command(JsonFixtureUpsertCommand):
    help = "Update Email Content from JSON fixture (system/fixtures/content/email_content.json)"
    fixture_key = "email_content"
    fixture_path = settings.BASE_DIR / "system" / "fixtures" / "content" / "email_content.json"
    model_path = "system.EmailContent"
    lookup_field = "key"
