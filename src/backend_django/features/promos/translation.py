"""Translation configuration for PromoMessage model."""

from modeltranslation.translator import TranslationOptions, register

from .models import PromoMessage


@register(PromoMessage)
class PromoMessageTranslationOptions(TranslationOptions):
    """Configure translatable fields for PromoMessage."""

    fields = ("title", "description", "button_text")
