from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_servicecombo_promo_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicecategory",
            name="booking_start_time",
            field=models.TimeField(
                blank=True,
                help_text="Earliest start time for booking services in this category. Leave empty to use global hours.",
                null=True,
                verbose_name="booking start time",
            ),
        ),
    ]
