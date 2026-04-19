from django.apps import AppConfig


class CabinetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cabinet"

    def ready(self) -> None:
        # cabinet.py is auto-discovered by codex_django.cabinet via autodiscover_modules("cabinet").
        # Ensure dashboard data providers are loaded at startup.
        # Delay import to avoid RuntimeWarning: Accessing the database during app initialization
        import sys

        if any(
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
            return

        import cabinet.services.analytics  # noqa: F401
