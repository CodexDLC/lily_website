from .models import SiteSettings


def site_settings(request):
    """
    Returns global site settings (contacts, socials) to every template.
    Usage: {{ site_settings.phone }}
    """
    return {"site_settings": SiteSettings.load()}
