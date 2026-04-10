from typing import Any

from codex_django.core.sitemaps import BaseSitemap
from django.conf import settings
from django.utils import translation
from features.main.sitemaps import CategorySitemap


class StaticSitemap(BaseSitemap):
    """Sitemap for static pages that don't depend on models."""

    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return getattr(settings, "SITEMAP_STATIC_PAGES", ["home"])

    def get_urls(self, page: int | str = 1, site: Any = None, protocol: str | None = None) -> list[dict[str, Any]]:
        domain = self.get_domain(site)
        urls: list[dict[str, Any]] = super().get_urls(page=page, site=site, protocol=protocol)

        for url_info in urls:
            item = url_info["item"]
            actual_item: Any = item[0] if isinstance(item, list | tuple) else item

            alternates: list[dict[str, str]] = []
            for lang in self.languages:
                with translation.override(lang):
                    loc = self.location(actual_item)
                alternates.append({"lang_code": lang, "location": f"https://{domain}{loc}"})

            default_lang = getattr(settings, "SITEMAP_DEFAULT_LANGUAGE", settings.LANGUAGE_CODE)
            with translation.override(default_lang):
                alternates.append(
                    {"lang_code": "x-default", "location": f"https://{domain}{self.location(actual_item)}"}
                )

            url_info["alternates"] = alternates

        return urls


sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
}
