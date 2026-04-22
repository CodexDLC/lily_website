from typing import Any

from codex_django.core.i18n.discovery import translate_current_url
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_url(context: dict[str, Any], lang_code: str) -> str:
    """Backward-compatible wrapper around the library i18n URL helper."""
    return translate_current_url(context, lang_code)
