from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from core import context_processors
from features.main.sitemaps import CategorySitemap


@pytest.mark.unit
def test_debug_context_exposes_canonical_origin_without_trailing_slash(settings):
    settings.DEBUG = False
    settings.SITE_BASE_URL = "https://lily-salon.de/"

    context = context_processors.debug_mode(SimpleNamespace())

    assert context == {
        "DEBUG_MODE": False,
        "CANONICAL_BASE_URL": "https://lily-salon.de",
    }


@pytest.mark.unit
def test_static_content_context_uses_request_language(monkeypatch, settings):
    settings.CODEX_STATIC_TRANSLATION_MODEL = "system.StaticTranslation"
    model = object()
    manager = Mock()
    manager.load_cached.return_value = {"faq_page_title": "Fragen"}
    monkeypatch.setattr(context_processors.apps, "get_model", lambda model_path: model)
    monkeypatch.setattr(context_processors, "get_static_content_manager", lambda: manager)

    result = context_processors.static_content(SimpleNamespace(LANGUAGE_CODE="de-DE"))

    assert result == {"static_content": {"faq_page_title": "Fragen"}}
    manager.load_cached.assert_called_once_with(model, lang_code="de")


@pytest.mark.unit
def test_static_content_context_fails_closed(monkeypatch, settings):
    settings.CODEX_STATIC_TRANSLATION_MODEL = "system.StaticTranslation"
    monkeypatch.setattr(context_processors.apps, "get_model", Mock(side_effect=LookupError))

    assert context_processors.static_content(SimpleNamespace(LANGUAGE_CODE="de")) == {"static_content": {}}


@pytest.mark.unit
def test_static_content_context_without_model_is_empty(settings):
    settings.CODEX_STATIC_TRANSLATION_MODEL = ""

    assert context_processors.static_content(SimpleNamespace()) == {"static_content": {}}


@pytest.mark.unit
@pytest.mark.django_db
def test_category_sitemap_supports_direct_and_wrapped_items(category):
    sitemap = CategorySitemap()

    assert category in sitemap.items()
    assert sitemap.lastmod(category) is None
    assert sitemap.lastmod((category, "de")) is None
    assert sitemap.location(category).endswith(f"/services/{category.slug}/")
    assert sitemap.location([category, "de"]).endswith(f"/services/{category.slug}/")
