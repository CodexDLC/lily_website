from django.core.cache import cache
from features.system.models.site_settings import SiteSettings
from features.system.models.static_translation import StaticTranslation


def site_settings(request):
    """
    Exposes SiteSettings to all templates.
    """
    return {"site_settings": SiteSettings.load()}


def static_content(request):
    """
    Exposes all StaticTranslation objects to templates as a dictionary.
    Usage: {{ content.home_hero_title }}
    """
    # Try to get from cache first
    cache_key = f"static_content_{request.LANGUAGE_CODE}"
    content_dict = cache.get(cache_key)

    if content_dict is None:
        # Fetch all translations from DB
        try:
            translations = StaticTranslation.objects.all()
            content_dict = {t.key: t.text for t in translations}
            # Cache for 1 hour
            cache.set(cache_key, content_dict, 3600)
        except Exception:
            # Fallback if table doesn't exist yet
            content_dict = {}

    return {"content": content_dict}
