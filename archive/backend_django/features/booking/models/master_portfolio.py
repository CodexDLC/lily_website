"""Master portfolio (work examples) model."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from features.main.models import Service
from features.system.models.mixins import TimestampMixin
from features.system.services.images import optimize_image

from .master import Master


class MasterPortfolio(TimestampMixin, models.Model):
    """
    Master's portfolio images (work examples).
    Displayed in carousel on master detail page.
    """

    master = models.ForeignKey(
        Master, on_delete=models.CASCADE, related_name="portfolio_items", verbose_name=_("Master")
    )

    # === Image ===
    image = models.ImageField(
        upload_to="portfolio/",
        verbose_name=_("Portfolio Image"),
        help_text=_("Example of master's work (recommended: 1200x1200px)"),
    )

    # === Description (Translatable) ===
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Brief description of the work (technique, products used, etc.)"),
    )

    # === Service Link (Optional) ===
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="portfolio_examples",
        verbose_name=_("Related Service"),
        help_text=_("Link to service this example demonstrates"),
    )

    # === Display ===
    order = models.PositiveIntegerField(
        default=0, verbose_name=_("Display Order"), help_text=_("Lower numbers appear first")
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Active"), help_text=_("Show on master page"))

    # === Instagram Integration (Future) ===
    instagram_url = models.URLField(
        blank=True, verbose_name=_("Instagram Post URL"), help_text=_("Link to original Instagram post")
    )

    class Meta:
        verbose_name = _("Portfolio Item")
        verbose_name_plural = _("Portfolio Items")
        ordering = ["master", "order", "-created_at"]

    def __str__(self):
        service_name = self.service.title if self.service else _("General work")
        return f"{self.master.name} - {service_name}"

    def save(self, *args, **kwargs):
        if self.image:
            optimize_image(self.image, max_width=1600)
        super().save(*args, **kwargs)
