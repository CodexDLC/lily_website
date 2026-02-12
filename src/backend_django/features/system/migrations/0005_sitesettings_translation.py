from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0004_sitesettings_hiring"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="address_city_de",
            field=models.CharField(
                default="06366 Köthen (Anhalt)", max_length=255, null=True, verbose_name="City & ZIP"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="address_city_en",
            field=models.CharField(
                default="06366 Köthen (Anhalt)", max_length=255, null=True, verbose_name="City & ZIP"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="address_city_ru",
            field=models.CharField(
                default="06366 Köthen (Anhalt)", max_length=255, null=True, verbose_name="City & ZIP"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="address_city_uk",
            field=models.CharField(
                default="06366 Köthen (Anhalt)", max_length=255, null=True, verbose_name="City & ZIP"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_text_de",
            field=models.TextField(
                blank=True,
                default="Bist du talentiert und liebst deinen Job? Werde Teil unseres Teams!",
                null=True,
                verbose_name="Hiring Text",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_text_en",
            field=models.TextField(
                blank=True,
                default="Bist du talentiert und liebst deinen Job? Werde Teil unseres Teams!",
                null=True,
                verbose_name="Hiring Text",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_text_ru",
            field=models.TextField(
                blank=True,
                default="Bist du talentiert und liebst deinen Job? Werde Teil unseres Teams!",
                null=True,
                verbose_name="Hiring Text",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_text_uk",
            field=models.TextField(
                blank=True,
                default="Bist du talentiert und liebst deinen Job? Werde Teil unseres Teams!",
                null=True,
                verbose_name="Hiring Text",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_title_de",
            field=models.CharField(
                blank=True, default="Wir suchen Verstärkung!", max_length=255, null=True, verbose_name="Hiring Title"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_title_en",
            field=models.CharField(
                blank=True, default="Wir suchen Verstärkung!", max_length=255, null=True, verbose_name="Hiring Title"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_title_ru",
            field=models.CharField(
                blank=True, default="Wir suchen Verstärkung!", max_length=255, null=True, verbose_name="Hiring Title"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_title_uk",
            field=models.CharField(
                blank=True, default="Wir suchen Verstärkung!", max_length=255, null=True, verbose_name="Hiring Title"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_saturday_de",
            field=models.CharField(default="10:00 - 14:00", max_length=100, null=True, verbose_name="Saturday"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_saturday_en",
            field=models.CharField(default="10:00 - 14:00", max_length=100, null=True, verbose_name="Saturday"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_saturday_ru",
            field=models.CharField(default="10:00 - 14:00", max_length=100, null=True, verbose_name="Saturday"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_saturday_uk",
            field=models.CharField(default="10:00 - 14:00", max_length=100, null=True, verbose_name="Saturday"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_sunday_de",
            field=models.CharField(default="Geschlossen", max_length=100, null=True, verbose_name="Sunday"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_sunday_en",
            field=models.CharField(default="Geschlossen", max_length=100, null=True, verbose_name="Sunday"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_sunday_ru",
            field=models.CharField(default="Geschlossen", max_length=100, null=True, verbose_name="Sunday"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_sunday_uk",
            field=models.CharField(default="Geschlossen", max_length=100, null=True, verbose_name="Sunday"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_weekdays_de",
            field=models.CharField(default="09:00 - 18:00", max_length=100, null=True, verbose_name="Mo-Fr"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_weekdays_en",
            field=models.CharField(default="09:00 - 18:00", max_length=100, null=True, verbose_name="Mo-Fr"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_weekdays_ru",
            field=models.CharField(default="09:00 - 18:00", max_length=100, null=True, verbose_name="Mo-Fr"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="working_hours_weekdays_uk",
            field=models.CharField(default="09:00 - 18:00", max_length=100, null=True, verbose_name="Mo-Fr"),
        ),
    ]
