from django.core.management import call_command
from django.db import migrations


def load_initial_owner(apps, schema_editor):
    call_command("loaddata", "initial_owner.json")


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0001_initial"),
        ("main", "0002_load_initial_data"),  # Ensure categories exist
    ]

    operations = [
        migrations.RunPython(load_initial_owner),
    ]
