"""Translation configuration for booking app models."""

from modeltranslation.translator import TranslationOptions, register

from .models import Master, MasterCertificate, MasterPortfolio


@register(Master)
class MasterTranslationOptions(TranslationOptions):
    """Translation fields for Master model."""

    fields = (
        "title",
        "bio",
        "short_description",
        "seo_title",
        "seo_description",
    )


@register(MasterCertificate)
class MasterCertificateTranslationOptions(TranslationOptions):
    """Translation fields for MasterCertificate model."""

    fields = ("title", "issuer")


@register(MasterPortfolio)
class MasterPortfolioTranslationOptions(TranslationOptions):
    """Translation fields for MasterPortfolio model."""

    fields = ("description",)
