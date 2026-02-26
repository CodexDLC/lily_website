from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0005_master_work_days"),
    ]

    operations = [
        migrations.AddField(
            model_name="master",
            name="is_public",
            field=models.BooleanField(
                default=True,
                db_index=True,
                verbose_name="Visible on Site",
                help_text="If unchecked, master participates in booking but is not shown publicly or on the team page",
            ),
        ),
    ]
