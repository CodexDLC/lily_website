import uuid

from django.db import migrations, models


def generate_unique_unsubscribe_tokens(apps, schema_editor):
    Client = apps.get_model("system", "Client")
    for client in Client.objects.all():
        client.unsubscribe_token = uuid.uuid4()
        client.save(update_fields=["unsubscribe_token"])


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
                null=True,
                verbose_name="unsubscribe token",
            ),
        ),
        migrations.RunPython(generate_unique_unsubscribe_tokens, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
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
