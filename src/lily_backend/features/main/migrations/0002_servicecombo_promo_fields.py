# Generated manually for ServiceCombo promo display fields.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicecombo",
            name="is_featured",
            field=models.BooleanField(default=False, verbose_name="featured promo"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_button_text",
            field=models.CharField(default="Termin buchen", max_length=80, verbose_name="promo button text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_button_text_de",
            field=models.CharField(default="Termin buchen", max_length=80, null=True, verbose_name="promo button text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_button_text_en",
            field=models.CharField(default="Termin buchen", max_length=80, null=True, verbose_name="promo button text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_button_text_ru",
            field=models.CharField(default="Termin buchen", max_length=80, null=True, verbose_name="promo button text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_button_text_uk",
            field=models.CharField(default="Termin buchen", max_length=80, null=True, verbose_name="promo button text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_image",
            field=models.ImageField(blank=True, null=True, upload_to="combos/", verbose_name="promo image"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_order",
            field=models.PositiveIntegerField(default=0, verbose_name="promo order"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_text",
            field=models.TextField(blank=True, verbose_name="promo text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_text_de",
            field=models.TextField(blank=True, null=True, verbose_name="promo text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_text_en",
            field=models.TextField(blank=True, null=True, verbose_name="promo text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_text_ru",
            field=models.TextField(blank=True, null=True, verbose_name="promo text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_text_uk",
            field=models.TextField(blank=True, null=True, verbose_name="promo text"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_title",
            field=models.CharField(blank=True, max_length=200, verbose_name="promo title"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_title_de",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="promo title"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_title_en",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="promo title"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_title_ru",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="promo title"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="promo_title_uk",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="promo title"),
        ),
        migrations.AddField(
            model_name="servicecombo",
            name="show_on_home",
            field=models.BooleanField(default=True, verbose_name="show on home page"),
        ),
    ]
