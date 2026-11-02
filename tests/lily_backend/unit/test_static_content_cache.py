import fakeredis
import pytest
from codex_platform.redis_service.operations.hash import HashOperations
from core.static_content_manager import ProjectStaticContentManager
from system.models import StaticTranslation


_REAL_ASYNC_HASH_GET_ALL = HashOperations.get_all


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


@pytest.mark.unit
def test_static_content_cache_uses_cached_mapping(fake_sync_redis, settings):
    settings.CODEX_REDIS_ENABLED = True
    manager = ProjectStaticContentManager(sync_client_factory=lambda: fake_sync_redis)
    cache_key = manager.make_key("static_content:de")
    fake_sync_redis.hset(cache_key, mapping={"faq_page_title": "FAQ"})

    assert manager.load_cached(StaticTranslation, lang_code="de") == {"faq_page_title": "FAQ"}


@pytest.mark.unit
def test_static_content_cache_mutations_are_language_scoped(fake_sync_redis, settings):
    settings.CODEX_REDIS_ENABLED = True
    manager = ProjectStaticContentManager(sync_client_factory=lambda: fake_sync_redis)
    de_key = manager.make_key("static_content:de")
    en_key = manager.make_key("static_content:en")

    manager.save_mapping({"title": "Titel"}, lang_code="de")
    manager.save_mapping({"title": "Title"}, lang_code="en")
    assert fake_sync_redis.hgetall(de_key) == {"title": "Titel"}
    assert fake_sync_redis.hgetall(en_key) == {"title": "Title"}

    manager.clear_language("de")
    assert fake_sync_redis.hgetall(de_key) == {}
    assert fake_sync_redis.hgetall(en_key) == {"title": "Title"}

    manager.clear_all_languages()
    assert fake_sync_redis.hgetall(en_key) == {}


@pytest.mark.unit
def test_static_content_cache_disabled_is_a_noop(fake_sync_redis, settings):
    settings.DEBUG = True
    settings.CODEX_REDIS_ENABLED = False
    manager = ProjectStaticContentManager(sync_client_factory=lambda: fake_sync_redis)

    assert manager.load_cached(StaticTranslation, lang_code="de") == {}
    manager.save_mapping({"title": "Titel"}, lang_code="de")
    manager.clear_language("de")
    manager.clear_all_languages()

    assert fake_sync_redis.hgetall(manager.make_key("static_content:de")) == {}


@pytest.mark.unit
def test_static_content_cache_falls_back_for_unsupported_language(fake_sync_redis, settings):
    settings.CODEX_REDIS_ENABLED = True
    settings.LANGUAGE_CODE = "de"
    settings.LANGUAGES = [("de", "Deutsch"), ("en", "English")]
    manager = ProjectStaticContentManager(sync_client_factory=lambda: fake_sync_redis)

    assert manager._cache_key_for_lang("fr-CA") == "static_content:de"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_static_content_cache_async_round_trip(monkeypatch, settings):
    settings.CODEX_REDIS_ENABLED = True
    server = fakeredis.FakeServer()
    monkeypatch.setattr(HashOperations, "get_all", _REAL_ASYNC_HASH_GET_ALL)

    def make_client():
        return fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)

    manager = ProjectStaticContentManager(async_client_factory=make_client)

    await manager.asave_mapping({"title": "Titel"}, lang_code="de")

    assert await manager.aload_cached(StaticTranslation, lang_code="de") == {"title": "Titel"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_static_content_cache_async_disabled_is_a_noop(settings):
    settings.DEBUG = True
    settings.CODEX_REDIS_ENABLED = False
    manager = ProjectStaticContentManager(
        async_client_factory=lambda: fakeredis.aioredis.FakeRedis(decode_responses=True)
    )

    await manager.asave_mapping({"title": "Titel"}, lang_code="de")

    assert await manager.aload_cached(StaticTranslation, lang_code="de") == {}
