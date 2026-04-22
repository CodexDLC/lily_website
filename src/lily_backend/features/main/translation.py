"""modeltranslation registrations for the main feature."""

from modeltranslation.translator import TranslationOptions, register

from .models import Service, ServiceCategory, ServiceCombo


@register(ServiceCategory)
class ServiceCategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description", "content", "seo_title", "seo_description")


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = ("name", "price_info", "duration_info", "description", "content", "seo_title", "seo_description")


@register(ServiceCombo)
class ServiceComboTranslationOptions(TranslationOptions):
    fields = ("name", "description")
