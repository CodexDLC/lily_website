from django import template
from django.urls import translate_url as django_translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_url(context, lang_code):
    """Translate current request path to another language.

    Usage: {% translate_url 'de' %}
    """
    request = context.get("request")
    if not request:
        return ""
    return django_translate_url(request.path, lang_code)
