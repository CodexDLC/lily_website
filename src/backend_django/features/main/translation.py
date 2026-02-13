from modeltranslation.translator import TranslationOptions, register

from .models import Category, PortfolioImage, Service


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("title", "description", "content", "seo_title", "seo_description")


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = ("title", "price_info", "duration_info", "description", "content", "seo_title", "seo_description")


@register(PortfolioImage)
class PortfolioImageTranslationOptions(TranslationOptions):
    fields = ("title",)
