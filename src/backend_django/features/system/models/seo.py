from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _

from .mixins import SeoMixin, TimestampMixin


class StaticPageSeo(TimestampMixin, SeoMixin):
    """
    SEO settings for static pages (Home, Contacts, etc.) that don't have their own models.
    """

    KEY_HOME = "home"
    KEY_CONTACTS = "contacts"
    KEY_TEAM = "team"
    KEY_SERVICES_INDEX = "services_index"
    KEY_IMPRESSUM = "impressum"
    KEY_DATENSCHUTZ = "datenschutz"

    PAGE_CHOICES = [
        (KEY_HOME, _("Home Page")),
        (KEY_CONTACTS, _("Contacts Page")),
        (KEY_TEAM, _("Team Page")),
        (KEY_SERVICES_INDEX, _("Services List Page")),
        (KEY_IMPRESSUM, _("Impressum")),
        (KEY_DATENSCHUTZ, _("Datenschutz")),
    ]

    page_key = models.CharField(
        max_length=50,
        choices=PAGE_CHOICES,
        unique=True,
        verbose_name=_("Page Key"),
        help_text=_("Unique identifier for the static page."),
    )

    class Meta:
        verbose_name = _("Static Page SEO")
        verbose_name_plural = _("Static Pages SEO")

    def __str__(self):
        return self.get_page_key_display()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Targeted cache invalidation
        cache.delete_many(["seo_static_pages_cache", f"seo_page_{self.page_key}"])
