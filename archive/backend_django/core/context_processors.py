from core.logger import log
from django.conf import settings


def seo_settings(request):
    """
    Adds SEO-related settings to the context.
    """
    # We use debug level here as this runs on every request
    log.debug(f"ContextProcessor: seo_settings | Action: Process | path={request.path}")

    return {
        "CANONICAL_DOMAIN": getattr(settings, "CANONICAL_DOMAIN", "https://lily-salon.de"),
    }
