from modeltranslation.translator import TranslationOptions, register

from .models.email_content import EmailContent
from .models.seo import StaticPageSeo
from .models.settings import SiteSettings
from .models.static import StaticTranslation


@register(StaticPageSeo)
class StaticPageSeoTranslationOptions(TranslationOptions):
    fields = ("seo_title", "seo_description")


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        "working_hours_weekdays",
        "working_hours_saturday",
        "working_hours_sunday",
        "hiring_title",
        "hiring_text",
    )


@register(StaticTranslation)
class StaticTranslationOptions(TranslationOptions):
    fields = ("content",)


@register(EmailContent)
class EmailContentTranslationOptions(TranslationOptions):
    fields = ("text",)
