from django.core.cache import cache
from django.db.utils import ProgrammingError
from loguru import logger as log

from .models import StaticTranslation
from .redis_managers.site_settings_manager import SiteSettingsManager


def site_settings(request):
    """
    Exposes SiteSettings to all templates from Redis.
    Usage: {{ site_settings.phone }}
    """
    return {"site_settings": SiteSettingsManager.load_from_redis()}


def static_content(request):
    """
    Exposes all StaticTranslation objects to templates as a dictionary.
    Usage: {{ content.home_hero_title }}
    """
    # Try to get from cache first
    cache_key = f"static_content_{request.LANGUAGE_CODE}"
    content_dict = cache.get(cache_key)

    if content_dict is None:
        try:
            # We fetch all objects to let django-modeltranslation handle the language.
            translations = StaticTranslation.objects.all()
            content_dict = {t.key: t.text for t in translations}

            # Cache for 1 hour
            cache.set(cache_key, content_dict, 3600)
        except ProgrammingError:
            # Table doesn't exist yet (e.g. during initial migrations)
            content_dict = {}
        except Exception as e:
            log.error(f"Error loading static content: {e}")
            content_dict = {}

    return {"content": content_dict}
