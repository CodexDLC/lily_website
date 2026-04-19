from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0004_masterdayoff"),
    ]

    operations = [
        migrations.AddField(
            model_name="master",
            name="work_days",
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name="Working Days",
                help_text="List of weekday numbers the master works (0=Mon … 6=Sun)",
            ),
        ),
    ]
