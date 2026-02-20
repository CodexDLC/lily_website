from datetime import time
from decimal import Decimal, InvalidOperation
from typing import Any

from django_redis import get_redis_connection

REDIS_SITE_SETTINGS_KEY = "site_settings_hash"


class SiteSettingsManager:
    """
    Manager for handling SiteSettings in Redis.
    Relocated from services/redis_site_settings.py to redis_managers/.
    """

    @staticmethod
    def get_redis_client():
        """
        Возвращает настроенный клиент Redis из Django CACHES.
        """
        return get_redis_connection("default")

    @classmethod
    def save_to_redis(cls, site_settings_instance: Any):
        """
        Сохраняет все значимые поля SiteSettings в Redis Hash.
        """
        redis_client = cls.get_redis_client()
        settings_dict = site_settings_instance.to_dict()

        # Преобразуем все значения в строки для хранения в Redis
        sanitized_dict = {}
        for key, value in settings_dict.items():
            if value is None:
                sanitized_dict[key] = ""
            elif isinstance(value, bool):
                sanitized_dict[key] = "true" if value else "false"
            else:
                sanitized_dict[key] = str(value)

        redis_client.hset(REDIS_SITE_SETTINGS_KEY, mapping=sanitized_dict)

    @classmethod
    def load_from_redis(cls) -> dict:
        """
        Загружает настройки сайта из Redis. Если их нет, загружает из БД и кэширует.
        """
        redis_client = cls.get_redis_client()
        cached_data = redis_client.hgetall(REDIS_SITE_SETTINGS_KEY)

        if cached_data:
            settings_dict: dict[str, Any] = {}
            for key, value in cached_data.items():
                decoded_key = key.decode("utf-8")
                decoded_value = value.decode("utf-8")

                if decoded_key in ["latitude", "longitude"]:
                    try:
                        settings_dict[decoded_key] = Decimal(decoded_value)
                    except (ValueError, TypeError, InvalidOperation):
                        settings_dict[decoded_key] = decoded_value
                elif decoded_key.startswith("work_") and decoded_key.endswith(("_weekdays", "_saturday")):
                    try:
                        settings_dict[decoded_key] = time.fromisoformat(decoded_value)
                    except (ValueError, TypeError):
                        settings_dict[decoded_key] = decoded_value
                elif decoded_value.lower() in ("true", "false"):
                    settings_dict[decoded_key] = decoded_value.lower() == "true"
                elif decoded_value.isdigit():
                    settings_dict[decoded_key] = int(decoded_value)
                else:
                    settings_dict[decoded_key] = decoded_value
            return settings_dict
        else:
            from features.system.models.site_settings import SiteSettings

            site_settings_instance = SiteSettings.load()
            cls.save_to_redis(site_settings_instance)
            return site_settings_instance.to_dict()
