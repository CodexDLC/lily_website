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

        from django.db.models.signals import post_delete, post_migrate, post_save

        from features.main.cabinet import refresh_catalog_categories, register_catalog_shell
        from features.main.models import ServiceCategory

        # 1. Register static shell items (safe, no DB)
        register_catalog_shell()

        # 2. Connect signals for runtime dynamic updates
        def update_sidebar(sender: Any, **kwargs: Any) -> None:
            refresh_catalog_categories()

        post_save.connect(update_sidebar, sender=ServiceCategory)
        post_delete.connect(update_sidebar, sender=ServiceCategory)

        # 3. Refresh categories after migrations are complete
        post_migrate.connect(lambda **kwargs: refresh_catalog_categories(), sender=self)
