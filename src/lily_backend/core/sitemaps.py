from codex_django.core.sitemaps import BaseSitemap
from django.conf import settings
from features.main.sitemaps import CategorySitemap


class StaticSitemap(BaseSitemap):
    """Project sitemap backed by the shared codex-django base sitemap."""

    priority = 0.8
    changefreq = "monthly"

    def items(self) -> list[str]:
        return list(getattr(settings, "SITEMAP_STATIC_PAGES", ("home",)))


sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
}
