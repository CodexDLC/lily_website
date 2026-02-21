from django.db import models
from django.utils.translation import gettext_lazy as _


class StaticTranslation(models.Model):
    """
    Model to store static text content that needs to be editable via Admin
    and translated into multiple languages without bloating .po files.
    """

    key = models.CharField(
        _("Key"),
        max_length=100,
        unique=True,
        help_text=_("Unique identifier used in templates (e.g., 'home_hero_title')"),
    )
    text = models.TextField(_("Text Content"), help_text=_("The actual text to be displayed and translated."))
    description = models.CharField(
        _("Description"), max_length=255, blank=True, help_text=_("Optional note about where this text is used.")
    )

    class Meta:
        verbose_name = _("Static Translation")
        verbose_name_plural = _("Static Translations")
        ordering = ["key"]

    def __str__(self):
        return self.key
