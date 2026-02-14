from features.system.services.redis_site_settings import load_site_settings_from_redis


def site_settings(request):
    """
    Returns global site settings (contacts, socials) to every template.
    Usage: {{ site_settings.phone }}
    """
    return {"site_settings": load_site_settings_from_redis()}
