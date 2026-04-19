from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ConversationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.conversations"
    verbose_name = _("Conversations")

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
            import features.conversations.services.notifications  # noqa
            import features.conversations.cabinet  # noqa
