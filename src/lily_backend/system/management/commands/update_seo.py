from codex_django.system.management import JsonFixtureUpsertCommand
from django.conf import settings


class Command(JsonFixtureUpsertCommand):
    help = "Update Static Page SEO from JSON fixture (system/fixtures/seo/static_pages_seo.json)"
    fixture_key = "static_pages_seo"
    fixture_path = settings.BASE_DIR / "system" / "fixtures" / "seo" / "static_pages_seo.json"
    model_path = "system.StaticPageSeo"
    lookup_field = "page_key"
