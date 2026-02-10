"""
Base model mixins for the project.

Usage:
    from features.system.models.mixins import TimestampMixin, ActiveMixin, SeoMixin

    class MyModel(TimestampMixin, ActiveMixin, SeoMixin, models.Model):
        ...
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampMixin(models.Model):
    """Adds created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        abstract = True


class ActiveMixin(models.Model):
    """
    Adds status fields:
    - is_active: Globally visible or hidden (e.g. no license).
    - is_available: Visible but booking disabled (e.g. no masters).
    - is_planned: Visible with 'Coming Soon' badge.
    """

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("If unchecked, this item will be completely hidden from the site."),
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name=_("Available for Booking"),
        help_text=_("If unchecked, shows 'Temporarily Unavailable' (e.g. no masters)."),
    )
    is_planned = models.BooleanField(
        default=False, verbose_name=_("Planned / Coming Soon"), help_text=_("If checked, shows 'Coming Soon' badge.")
    )

    class Meta:
        abstract = True


class SeoMixin(models.Model):
    """Adds SEO fields (title, description, OG image)."""

    seo_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("SEO Title"),
        help_text=_("Browser tab title. Defaults to object title if empty."),
    )
    seo_description = models.TextField(
        blank=True, verbose_name=_("SEO Description"), help_text=_("Meta description for search engines.")
    )
    seo_image = models.ImageField(
        upload_to="seo/",
        blank=True,
        null=True,
        verbose_name=_("OG Image"),
        help_text=_("Image for social media sharing (1200x630px recommended)."),
    )

    class Meta:
        abstract = True
