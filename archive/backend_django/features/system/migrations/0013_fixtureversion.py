from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0012_emailcontent"),
    ]

    operations = [
        migrations.CreateModel(
            name="FixtureVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("content_hash", models.CharField(max_length=64)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
