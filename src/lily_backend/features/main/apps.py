from typing import Any

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.main"
    verbose_name = _("Main")

    def ready(self) -> None:
        # Explicitly import translation to ensure models are registered for modeltranslation
        import features.main.translation  # noqa
        import modeltranslation  # noqa

        import features.main.cabinet  # noqa

        # Connect signals to update cabinet sidebar whenever categories change
        from django.db.models.signals import post_delete, post_save

        from features.main.cabinet import register_cabinet_catalog
        from features.main.models import ServiceCategory

        def update_sidebar(sender: Any, **kwargs: Any) -> None:
            register_cabinet_catalog()

        post_save.connect(update_sidebar, sender=ServiceCategory)
        post_delete.connect(update_sidebar, sender=ServiceCategory)
