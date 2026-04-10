"""Scaffold-owned app configuration for resource-slot booking."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BookingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.booking"
    verbose_name = _("Resource-Slot Booking")
