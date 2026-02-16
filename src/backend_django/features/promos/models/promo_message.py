"""PromoMessage model for promotional banners and announcements."""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import TimestampMixin


class PromoMessage(TimestampMixin, models.Model):
    """
    Model for promotional promos (floating buttons, modal windows, banners).

    Used to show time-limited promotions, special offers, and announcements to website visitors.
    """

    # --- Content ---
    title = models.CharField(_("Title"), max_length=255, help_text=_("Main title of the promotion"))

    description = models.TextField(_("Description"), help_text=_("Full description shown in the modal window"))

    button_text = models.CharField(
        _("Button Text"),
        max_length=100,
        default="Акция!",
        help_text=_("Text displayed on the floating button"),
    )

    # --- Status & Visibility ---
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("If unchecked, the notification will not be shown even if within the date range"),
    )

    # --- Scheduling ---
    starts_at = models.DateTimeField(
        _("Start Date"),
        default=timezone.now,
        help_text=_("When to start showing this notification"),
    )

    ends_at = models.DateTimeField(
        _("End Date"),
        help_text=_("When to stop showing this notification"),
    )

    display_delay = models.PositiveIntegerField(
        _("Display Delay (seconds)"),
        default=3,
        validators=[MinValueValidator(0)],
        help_text=_("How many seconds to wait after page load before showing the button"),
    )

    # --- Targeting ---
    target_pages = models.TextField(
        _("Target Pages"),
        blank=True,
        help_text=_(
            "Comma-separated list of page slugs (e.g., 'home,services,team'). Leave empty to show on all pages."
        ),
    )

    priority = models.IntegerField(
        _("Priority"),
        default=0,
        help_text=_("Higher priority promos are shown first if multiple are active (higher number = higher priority)"),
    )

    # --- Design ---
    button_color = models.CharField(
        _("Button Background Color"),
        max_length=7,
        default="#EDD071",
        help_text=_("Hex color code (e.g., #EDD071)"),
    )

    text_color = models.CharField(
        _("Button Text Color"),
        max_length=7,
        default="#003831",
        help_text=_("Hex color code (e.g., #003831)"),
    )

    image = models.ImageField(
        _("Image"),
        upload_to="promos/",
        blank=True,
        null=True,
        help_text=_("Optional image to display in the modal window"),
    )

    # --- Analytics ---
    views_count = models.PositiveIntegerField(
        _("Views Count"),
        default=0,
        help_text=_("How many times the floating button was displayed"),
    )

    clicks_count = models.PositiveIntegerField(
        _("Clicks Count"),
        default=0,
        help_text=_("How many times the modal window was opened"),
    )

    class Meta:
        verbose_name = _("Promo Notification")
        verbose_name_plural = _("Promo Notifications")
        ordering = ["-priority", "-starts_at"]

    def __str__(self):
        return f"{self.title} ({self.starts_at.strftime('%Y-%m-%d')} - {self.ends_at.strftime('%Y-%m-%d')})"

    @property
    def is_currently_active(self) -> bool:
        """Check if notification is active and within the date range."""
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at

    @property
    def status_display(self) -> str:
        """Human-readable status for display."""
        if not self.is_active:
            return _("Inactive")

        now = timezone.now()
        if now < self.starts_at:
            return _("Scheduled")
        elif now > self.ends_at:
            return _("Expired")
        else:
            return _("Active")

    @property
    def ctr(self) -> float:
        """Click-through rate (clicks / views)."""
        if self.views_count == 0:
            return 0.0
        return (self.clicks_count / self.views_count) * 100

    def clean(self):
        """Validate that ends_at is after starts_at."""
        from django.core.exceptions import ValidationError

        if self.ends_at and self.starts_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": _("End date must be after start date")})

    def save(self, *args, **kwargs):
        """Run validation before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
