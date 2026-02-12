from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0003_sitesettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_active",
            field=models.BooleanField(
                default=True, help_text="Show 'We are hiring' block on Team page", verbose_name="Hiring Active"
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_text",
            field=models.TextField(
                blank=True,
                default="Bist du talentiert und liebst deinen Job? Werde Teil unseres Teams!",
                verbose_name="Hiring Text",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hiring_title",
            field=models.CharField(
                blank=True, default="Wir suchen Verstärkung!", max_length=255, verbose_name="Hiring Title"
            ),
        ),
    ]
