from core.logger import log
from django.db import DatabaseError
from redis.exceptions import RedisError

from .redis_managers.site_settings_manager import SiteSettingsManager


def site_settings(request):
    """
    Returns global site settings (contacts, socials) to every template.
    Usage: {{ site_settings.phone }}
    """
    try:
        return {"site_settings": SiteSettingsManager.load_from_redis()}
    except RedisError as e:
        log.error(f"Redis unavailable in site_settings context processor: {e}")
        try:
            from features.system.models.site_settings import SiteSettings

            return {"site_settings": SiteSettings.load().to_dict()}
        except DatabaseError as e2:
            log.critical(f"DB also unavailable in site_settings context processor: {e2}")
            return {"site_settings": {}}
