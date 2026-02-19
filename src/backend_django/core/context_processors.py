from django.conf import settings


def seo_settings(request):
    """
    Adds SEO-related settings to the context.
    """
    return {
        "CANONICAL_DOMAIN": getattr(settings, "CANONICAL_DOMAIN", "https://lily-salon.de"),
    }
