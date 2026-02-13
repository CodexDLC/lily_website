from django.db import models
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import ActiveMixin, SeoMixin, TimestampMixin
from features.system.services.images import optimize_image

from .category import Category


class Service(TimestampMixin, ActiveMixin, SeoMixin):
    """
    Specific service (e.g. 'Classic Manicure').
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("Category"),
        help_text=_("Main category (for filtering)."),
    )
    title = models.CharField(
        max_length=255, verbose_name=_("Title"), help_text=_("Service name (e.g. 'Klassische Maniküre').")
    )
    slug = models.SlugField(unique=True, verbose_name=_("Slug"), help_text=_("URL part (e.g. 'classic-manicure')."))
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Price (€)"),
        help_text=_("Base price for sorting and calculation."),
    )
    price_info = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Price Display Text"),
        help_text=_("Text to display (e.g. 'ab 30€'). If empty, uses Price field."),
    )
    duration = models.PositiveIntegerField(verbose_name=_("Duration (min)"), help_text=_("Duration in minutes."))
    duration_info = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Duration Display Text"),
        help_text=_("Text to display (e.g. 'ca. 45-60 Min'). If empty, uses Duration field."),
    )
    description = models.TextField(
        blank=True, verbose_name=_("Short Description"), help_text=_("Displayed in the list view.")
    )
    content = models.TextField(
        blank=True,
        verbose_name=_("Full Content"),
        help_text=_("Detailed description/article about the service (HTML/Markdown)."),
    )
    image = models.ImageField(
        upload_to="services/",
        blank=True,
        null=True,
        verbose_name=_("Image"),
        help_text=_("Photo of the specific service."),
    )
    is_hit = models.BooleanField(
        default=False, verbose_name=_("Hit / Popular"), help_text=_("Highlight this service as popular.")
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"), help_text=_("Sorting order."))

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.image:
            optimize_image(self.image, max_width=1200)
        super().save(*args, **kwargs)


class PortfolioImage(TimestampMixin):
    """
    Gallery images for a specific service (Before/After, Examples).
    Displayed as a Bento grid on the service detail page.
    """

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="portfolio_images", verbose_name=_("Service")
    )
    image = models.ImageField(
        upload_to="portfolio/", verbose_name=_("Image"), help_text=_("High quality photo. Will be resized by CSS.")
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Title / Description"),
        help_text=_("Optional caption for the image."),
    )
    order = models.PositiveIntegerField(
        default=0, verbose_name=_("Order"), help_text=_("Sorting order in the gallery.")
    )

    class Meta:
        verbose_name = _("Portfolio Image")
        verbose_name_plural = _("Portfolio Images")
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.service.title}"

    def save(self, *args, **kwargs):
        if self.image:
            optimize_image(self.image, max_width=1600)
        super().save(*args, **kwargs)
