import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from features.main.models import Category
from features.system.models.mixins import SeoMixin, TimestampMixin

User = get_user_model()


class Master(TimestampMixin, SeoMixin, models.Model):
    """
    Salon master/specialist.
    Can work without Django User (Telegram-only access).
    User is created only when master needs Django Admin access (future).
    """

    # === Basic Information ===
    name = models.CharField(
        max_length=255, verbose_name=_("Full Name"), help_text=_("Master's full name (e.g. 'Maria Ivanova')")
    )

    slug = models.SlugField(unique=True, verbose_name=_("Slug"), help_text=_("URL part (e.g. 'maria-ivanova')"))

    photo = models.ImageField(
        upload_to="masters/",
        blank=True,
        null=True,
        verbose_name=_("Profile Photo"),
        help_text=_("Professional portrait (recommended: 800x1000px)"),
    )

    # === Professional Info (Translatable) ===
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Professional Title"),
        help_text=_("e.g. 'Top Colorist', 'Lead Nail Artist'"),
    )

    bio = models.TextField(
        blank=True, verbose_name=_("Biography"), help_text=_("Full biography and work philosophy (HTML allowed)")
    )

    short_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Short Description"),
        help_text=_("Brief intro for Team page (1-2 sentences)"),
    )

    # === Specializations (What master can do) ===
    service_groups = models.ManyToManyField(
        "main.ServiceGroup",
        related_name="masters",
        blank=True,
        verbose_name=_("Service Groups"),
        help_text=_("Specific service groups this master can perform"),
    )

    categories = models.ManyToManyField(
        Category,
        related_name="masters",
        blank=True,
        verbose_name=_("Categories"),
        help_text=_("High-level categories for filtering"),
    )

    # === Experience ===
    years_experience = models.PositiveIntegerField(default=0, verbose_name=_("Years of Experience"))

    # === Contact (Optional) ===
    instagram = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Instagram Handle"),
        help_text=_("Username only (e.g. 'maria.beauty')"),
    )

    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Direct Phone"))

    # === Employment Status (instead of is_active) ===
    STATUS_ACTIVE = "active"
    STATUS_VACATION = "vacation"
    STATUS_FIRED = "fired"
    STATUS_TRAINING = "training"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, _("Active (Working)")),
        (STATUS_VACATION, _("On Vacation")),
        (STATUS_FIRED, _("Fired/Left")),
        (STATUS_TRAINING, _("In Training")),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True,
        verbose_name=_("Employment Status"),
        help_text=_("We never delete masters, only change status"),
    )

    # === Flags ===
    is_owner = models.BooleanField(
        default=False, verbose_name=_("Is Owner"), help_text=_("Display as salon owner with special styling")
    )

    is_featured = models.BooleanField(default=False, verbose_name=_("Featured Master"))

    # === Display Order ===
    order = models.PositiveIntegerField(
        default=0, verbose_name=_("Display Order"), help_text=_("Lower numbers appear first")
    )

    # === Django User Link (Optional - for future personal cabinet) ===
    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="master_profile",
        verbose_name=_("Django User Account"),
        help_text=_("Linked when master needs personal cabinet access"),
    )

    # === Telegram Bot Integration ===
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        verbose_name=_("Telegram ID"),
        help_text=_("For bot authentication and notifications"),
    )

    telegram_username = models.CharField(max_length=100, blank=True, verbose_name=_("Telegram Username"))

    bot_access_code = models.CharField(
        max_length=8,
        unique=True,
        editable=False,
        verbose_name=_("Bot Access Code"),
        help_text=_("One-time code for master registration in bot"),
    )

    # === QR Token (Future - for finalization) ===
    qr_token = models.CharField(max_length=32, unique=True, editable=False, verbose_name=_("QR Token"))

    class Meta:
        verbose_name = _("Master")
        verbose_name_plural = _("Masters")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Generate access codes on creation"""
        if not self.bot_access_code:
            import random

            self.bot_access_code = f"LILY{random.randint(1000, 9999)}"

        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex[:16].upper()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("master_detail", kwargs={"slug": self.slug})

    @property
    def instagram_url(self):
        """Full Instagram profile URL"""
        if self.instagram:
            return f"https://instagram.com/{self.instagram.lstrip('@')}"
        return None

    @property
    def is_available_for_booking(self):
        """Check if master can accept new bookings"""
        return self.status == self.STATUS_ACTIVE

    def get_available_services(self):
        """Get all services this master can perform"""
        from features.main.models import Service

        return Service.objects.filter(group__in=self.service_groups.all(), is_active=True).distinct()

    def can_perform_service(self, service):
        """Check if master can perform specific service"""
        return self.service_groups.filter(pk=service.group_id).exists()

    def active_portfolio_count(self):
        """Count of published portfolio images (future)"""
        # return self.portfolio_images.filter(is_active=True).count()
        return 0  # Placeholder
