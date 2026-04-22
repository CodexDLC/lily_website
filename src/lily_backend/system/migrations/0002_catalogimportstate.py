from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CatalogImportState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(db_index=True, max_length=100, unique=True, verbose_name="catalog key")),
                ("source_hash", models.CharField(max_length=64, verbose_name="source hash")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
            ],
            options={
                "verbose_name": "Catalog import state",
                "verbose_name_plural": "Catalog import states",
            },
        ),
    ]
