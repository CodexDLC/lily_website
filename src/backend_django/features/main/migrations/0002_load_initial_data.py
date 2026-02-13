import os

from django.core.management import call_command
from django.db import migrations


def load_initial_data(apps, schema_editor):
    # Path to the fixture file
    fixture_file = os.path.join(os.path.dirname(__file__), "../fixtures/initial_data.json")
    if os.path.exists(fixture_file):
        call_command("loaddata", fixture_file)


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
        ("booking", "0002_initial"),  # Ensure booking models are ready
        ("system", "0001_initial"),  # Ensure system models are ready
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
