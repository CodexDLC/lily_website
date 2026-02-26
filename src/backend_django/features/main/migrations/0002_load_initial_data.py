from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
        ("booking", "0001_initial"),  # Ensure booking models are ready
        ("system", "0001_initial"),  # Ensure system models are ready
    ]

    operations: list[migrations.operations.base.Operation] = [
        # migrations.RunPython(load_initial_data),  # Removed: Loading via management command instead
    ]
