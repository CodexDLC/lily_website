from modeltranslation.translator import TranslationOptions, register

from .models import Category, PortfolioImage, Service, ServiceGroup


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("title", "description", "content", "seo_title", "seo_description")


@register(ServiceGroup)
class ServiceGroupTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = ("title", "price_info", "description", "content", "seo_title", "seo_description")


@register(PortfolioImage)
class PortfolioImageTranslationOptions(TranslationOptions):
    fields = ("title",)
