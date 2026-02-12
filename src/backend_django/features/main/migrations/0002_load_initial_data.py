from django.core.management import call_command
from django.db import migrations


def load_initial_data(apps, schema_editor):
    call_command("loaddata", "initial_categories.json")
    call_command("loaddata", "initial_services.json")


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
