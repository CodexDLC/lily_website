"""modeltranslation registrations for the booking feature."""

from modeltranslation.translator import TranslationOptions, register

from .models import Master


@register(Master)
class MasterTranslationOptions(TranslationOptions):
    fields = ("title", "bio", "short_description", "seo_title", "seo_description")
