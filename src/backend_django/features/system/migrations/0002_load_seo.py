import json
import os

from django.db import migrations


def load_seo(apps, schema_editor):
    StaticPageSeo = apps.get_model("system", "StaticPageSeo")

    # Path to fixture file
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # features/system
        "fixtures",
        "initial_seo.json",
    )

    if not os.path.exists(fixture_path):
        print(f"Fixture not found: {fixture_path}")
        return

    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

        for item in data:
            fields = item["fields"]
            page_key = fields["page_key"]

            # Remove page_key from defaults as it's used for lookup
            defaults = fields.copy()
            del defaults["page_key"]

            StaticPageSeo.objects.get_or_create(page_key=page_key, defaults=defaults)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_seo, reverse_func),
    ]
