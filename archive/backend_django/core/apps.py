from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """
        Initialize Loguru logging when Django starts.
        Ensures it runs only once.
        """
        if not getattr(settings, "LOGURU_SETUP", False):
            from .logger import setup_logging

            setup_logging(
                base_dir=settings.BASE_DIR,
                config={
                    "LOG_LEVEL_CONSOLE": getattr(settings, "LOG_LEVEL_CONSOLE", "INFO"),
                    "LOG_LEVEL_FILE": getattr(settings, "LOG_LEVEL_FILE", "DEBUG"),
                    "LOG_ROTATION": getattr(settings, "LOG_ROTATION", "10 MB"),
                    "DEBUG": settings.DEBUG,
                },
            )
            # Mark as setup to prevent double initialization
            settings.LOGURU_SETUP = True
