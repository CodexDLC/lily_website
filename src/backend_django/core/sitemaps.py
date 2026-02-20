from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation


# Base class to force canonical domain and ensure xhtml:link generation
class BaseSitemap(Sitemap):
    i18n = True
    languages = [lang[0] for lang in settings.LANGUAGES]
    x_default = True

    def get_domain(self, site=None):
        # Always use the canonical domain from settings
        return settings.CANONICAL_DOMAIN.split("://")[-1]

    def get_urls(self, page=1, site=None, protocol=None):
        # Force HTTPS and use our canonical domain
        domain = self.get_domain(site)
        urls = super().get_urls(page=page, site=None, protocol="https")

        for url_info in urls:
            # url_info['item'] is (original_item, lang_code) because i18n=True
            item = url_info["item"]
            actual_item = item[0] if isinstance(item, list | tuple) else item

            alternates = []
            for lang in self.languages:
                with translation.override(lang):
                    # Call location with the original item
                    loc = self.location(actual_item)
                alternates.append({"lang_code": lang, "location": f"https://{domain}{loc}"})

            # Add x-default (pointing to German version)
            with translation.override("de"):
                alternates.append(
                    {"lang_code": "x-default", "location": f"https://{domain}{self.location(actual_item)}"}
                )

            url_info["alternates"] = alternates

        return urls

    def location(self, item):
        # Handle cases where Django passes (item, lang_code) tuple
        actual_item = item[0] if isinstance(item, list | tuple) else item
        if isinstance(actual_item, str):
            return reverse(actual_item)
        return actual_item.get_absolute_url()


class StaticSitemap(BaseSitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return ["home", "services", "team", "contacts", "booking_wizard", "impressum", "datenschutz"]


# Import CategorySitemap from features.main
# noqa: E402 (Module level import not at top of file) - Avoid circular import
from features.main.sitemaps import CategorySitemap  # noqa: E402

# Define the sitemaps dictionary
sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
}
