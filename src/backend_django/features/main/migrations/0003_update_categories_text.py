from django.core.management import call_command
from django.db import migrations


def update_categories_text(apps, schema_editor):
    call_command("loaddata", "initial_categories.json")


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_load_initial_data"),
    ]

    operations = [
        migrations.RunPython(update_categories_text),
    ]
