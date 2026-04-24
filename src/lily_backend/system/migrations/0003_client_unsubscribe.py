import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0002_catalogimportstate"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="unsubscribe_token",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="unsubscribe token",
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="email_opt_out_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="email opt-out at"),
        ),
    ]
