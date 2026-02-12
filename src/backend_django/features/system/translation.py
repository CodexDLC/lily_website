from modeltranslation.translator import TranslationOptions, register

from .models.seo import StaticPageSeo
from .models.site_settings import SiteSettings


@register(StaticPageSeo)
class StaticPageSeoTranslationOptions(TranslationOptions):
    fields = ("seo_title", "seo_description")


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        "hiring_title",
        "hiring_text",
        "working_hours_weekdays",
        "working_hours_saturday",
        "working_hours_sunday",
        "address_city",
    )
