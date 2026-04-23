from django.apps import apps
from django.conf import settings
from django.utils import translation

from core.static_content_manager import get_static_content_manager


def debug_mode(request):
    """
    Adds DEBUG_MODE to the template context.
    Provides a reliable way to check if we are in local development mode.
    """
    return {
        "DEBUG_MODE": settings.DEBUG,
        "CANONICAL_BASE_URL": settings.SITE_BASE_URL.rstrip("/"),
    }


def static_content(request):
    """
    Project-local static content loader with language-aware Redis caching.
    """
    model_path = getattr(settings, "CODEX_STATIC_TRANSLATION_MODEL", None)
    if not model_path:
        return {"static_content": {}}

    lang = (getattr(request, "LANGUAGE_CODE", None) or translation.get_language() or settings.LANGUAGE_CODE).split("-")[
        0
    ]

    try:
        model = apps.get_model(model_path)
        manager = get_static_content_manager()
        data = manager.load_cached(model, lang_code=lang)
        return {"static_content": data}
    except Exception:
        return {"static_content": {}}
