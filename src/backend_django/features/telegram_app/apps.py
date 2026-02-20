from django.apps import AppConfig


class TelegramAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features.telegram_app"
    verbose_name = "Telegram Mini App Integration"
