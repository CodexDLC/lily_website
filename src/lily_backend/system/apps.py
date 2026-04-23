from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "system"
    label = "system"
    verbose_name = _("Система")

    def ready(self) -> None:
        from core.static_content_manager import get_static_content_manager
        from django.db.models.signals import post_delete, post_save

        import system.translation  # noqa: F401
        from system.models import StaticTranslation

        def invalidate_static_translation_cache(**kwargs) -> None:
            get_static_content_manager().clear_all_languages()

        post_save.connect(
            invalidate_static_translation_cache,
            sender=StaticTranslation,
            dispatch_uid="system.static_translation.invalidate_cache_on_save",
        )
        post_delete.connect(
            invalidate_static_translation_cache,
            sender=StaticTranslation,
            dispatch_uid="system.static_translation.invalidate_cache_on_delete",
        )
