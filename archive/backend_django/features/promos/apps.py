"""Promos app configuration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PromosConfig(AppConfig):
    """Configuration for Promos app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "features.promos"
    verbose_name = _("Promos")
