from unittest.mock import patch

from codex_django.core.sitemaps import BaseSitemap
from core.sitemaps import StaticSitemap
from core.templatetags.i18n_urls import translate_url


def test_static_sitemap_is_library_backed():
    assert issubclass(StaticSitemap, BaseSitemap)


def test_translate_url_wrapper_uses_library_helper():
    context = {"request": object()}
    with patch("core.templatetags.i18n_urls.translate_current_url", return_value="/de/example/") as mocked_translate:
        result = translate_url(context, "de")

    assert result == "/de/example/"
    mocked_translate.assert_called_once_with(context, "de")
