from modeltranslation.translator import TranslationOptions, register

from .models.seo import StaticPageSeo


@register(StaticPageSeo)
class StaticPageSeoTranslationOptions(TranslationOptions):
    fields = ("seo_title", "seo_description")
