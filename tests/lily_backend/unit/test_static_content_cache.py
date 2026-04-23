import pytest
from core.static_content_manager import ProjectStaticContentManager
from system.models import StaticTranslation


@pytest.mark.unit
@pytest.mark.django_db
def test_static_content_cache_is_language_aware(fake_sync_redis, settings):
    settings.CODEX_REDIS_ENABLED = True

    StaticTranslation.objects.create(
        key="home_hero_uptitle",
        content="Premium Beauty Salon",
        content_de="Premium Beauty Salon",
        content_en="Premium Beauty Salon",
        content_ru="Премиум салон красоты",
        content_uk="Преміум салон краси",
    )

    manager = ProjectStaticContentManager(sync_client_factory=lambda: fake_sync_redis)

    de_data = manager.load_cached(StaticTranslation, lang_code="de")
    ru_data = manager.load_cached(StaticTranslation, lang_code="ru")

    assert de_data["home_hero_uptitle"] == "Premium Beauty Salon"
    assert ru_data["home_hero_uptitle"] == "Премиум салон красоты"

    de_key = manager.make_key("static_content:de")
    ru_key = manager.make_key("static_content:ru")

    assert fake_sync_redis.hgetall(de_key)["home_hero_uptitle"] == "Premium Beauty Salon"
    assert fake_sync_redis.hgetall(ru_key)["home_hero_uptitle"] == "Премиум салон красоты"
