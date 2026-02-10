"""Load initial owner data (Liliia Yakina)."""

from django.db import migrations


def load_fixture(apps, schema_editor):
    """Load initial_owner.json fixture."""
    Master = apps.get_model("booking", "Master")

    # Create owner (Liliia Yakina)
    Master.objects.create(
        id=1,
        name="Liliia Yakina",
        slug="liliia-yakina",
        photo="masters/lily.webp",
        title_de="Gründerin & Art Director",
        title_en="Founder & Art Director",
        title_ru="Основатель и Арт-директор",
        title_uk="Засновник і Арт-директор",
        bio_de="Willkommen im LILY Beauty Space. Hier kreieren wir nicht nur Looks, sondern Stimmungen. Meine Mission ist es, Ihnen Selbstvertrauen und höchste Servicequalität in einer gemütlichen Atmosphäre zu schenken.",
        bio_en="Welcome to LILY Beauty Space. Here we create not just looks, but moods. My mission is to give you confidence and the highest quality of service in a cozy atmosphere.",
        bio_ru="Добро пожаловать в LILY Beauty Space. Здесь мы создаем не просто образы, а настроение. Моя миссия — подарить вам уверенность в себе и высочайшее качество сервиса в уютной атмосфере.",
        bio_uk="Ласкаво просимо до LILY Beauty Space. Тут ми створюємо не просто образи, а настрій. Моя місія — подарувати вам впевненість у собі та найвищу якість сервісу в затишній атмосфері.",
        short_description_de="Inhaberin und führende Meisterin des LILY Beauty Space",
        short_description_en="Owner and leading master of LILY Beauty Space",
        short_description_ru="Владелица и ведущий мастер LILY Beauty Space",
        short_description_uk="Власниця та провідний майстер LILY Beauty Space",
        years_experience=10,
        instagram="manikure_kothen",
        phone="+49 176 59423704",
        status="active",
        is_owner=True,
        is_featured=True,
        order=0,
        telegram_id=1015694494,
        telegram_username="Lily_prekrasnay",
        bot_access_code="LILY0001",
        qr_token="OWNER001",
    )


def unload_fixture(apps, schema_editor):
    """Remove owner data on migration rollback."""
    Master = apps.get_model("booking", "Master")
    Master.objects.filter(is_owner=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_fixture, reverse_code=unload_fixture),
    ]
