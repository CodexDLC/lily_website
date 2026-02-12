import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0001_initial"),
        ("main", "0003_update_categories_text"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                (
                    "topic",
                    models.CharField(
                        choices=[
                            ("general", "General Question"),
                            ("booking", "Booking Inquiry"),
                            ("job", "Job / Career"),
                            ("other", "Other"),
                        ],
                        default="general",
                        max_length=50,
                        verbose_name="Topic",
                    ),
                ),
                ("message", models.TextField(blank=True, verbose_name="Message")),
                ("is_processed", models.BooleanField(default=False, verbose_name="Processed")),
                ("admin_notes", models.TextField(blank=True, verbose_name="Admin Notes")),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contact_requests",
                        to="booking.client",
                        verbose_name="Client",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contact Request",
                "verbose_name_plural": "Contact Requests",
                "ordering": ["-created_at"],
            },
        ),
    ]
