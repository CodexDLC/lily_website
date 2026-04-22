"""Scaffold-owned app configuration for resource-slot booking."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BookingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.booking"
    verbose_name = _("Resource-Slot Booking")

    def ready(self):
        import sys

        if not any(
            arg in sys.argv
            for arg in [
                "migrate",
                "collectstatic",
                "makemigrations",
                "check",
                "migrate_all_legacy",
                "migrate_users",
                "test",
            ]
        ):
            import features.booking.services.notifications  # noqa
            import features.booking.cabinet  # noqa
