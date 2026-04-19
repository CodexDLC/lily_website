from django.conf import settings


def debug_mode(request):
    """
    Adds DEBUG_MODE to the template context.
    Provides a reliable way to check if we are in local development mode.
    """
    return {"DEBUG_MODE": settings.DEBUG}
