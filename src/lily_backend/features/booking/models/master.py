import secrets
import uuid
from typing import Any, ClassVar

from codex_django.booking.mixins import AbstractBookableMaster
from codex_django.core.mixins.models import SeoMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from features.main.models import ServiceCategory


class Master(SeoMixin, AbstractBookableMaster):
    STATUS_ACTIVE = "active"
    STATUS_VACATION = "vacation"
    STATUS_TRAINING = "training"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES: ClassVar[list[tuple[str, Any]]] = [
        (STATUS_ACTIVE, _("Active")),
        (STATUS_VACATION, _("On Vacation")),
        (STATUS_TRAINING, _("In Training")),
        (STATUS_INACTIVE, _("Inactive")),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="master_profile",
        verbose_name=_("user"),
    )
    name = models.CharField(_("name"), max_length=255)
    title = models.CharField(
        _("professional title"), max_length=255, blank=True, help_text=_("e.g. 'Top Colorist', 'Leiterin & Inhaberin'")
    )
    slug = models.SlugField(_("slug"), unique=True)
    photo = models.ImageField(_("photo"), upload_to="masters/", blank=True, null=True)
    bio = models.TextField(_("biography"), blank=True)
    short_description = models.CharField(_("short description"), max_length=500, blank=True)
    categories = models.ManyToManyField(
        ServiceCategory,
        blank=True,
        related_name="masters",
        verbose_name=_("categories"),
    )
    years_experience = models.PositiveIntegerField(_("years of experience"), default=0)
    instagram = models.CharField(_("instagram handle"), max_length=100, blank=True)
    phone = models.CharField(_("direct phone"), max_length=20, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True,
    )
    is_owner = models.BooleanField(_("is owner"), default=False)
    is_featured = models.BooleanField(_("featured"), default=False)
    is_public = models.BooleanField(_("visible on site"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("display order"), default=0)
    booking_priority = models.PositiveSmallIntegerField(
        _("booking priority"),
        default=100,
        db_index=True,
        help_text=_(
            "Lower value = booked first. Controls which master receives new bookings first (fill_first strategy)."
        ),
    )

    # Telegram
    telegram_id = models.BigIntegerField(_("telegram ID"), null=True, blank=True, unique=True, db_index=True)
    telegram_username = models.CharField(_("telegram username"), max_length=100, blank=True)
    bot_access_code = models.CharField(
        _("bot access code"),
        max_length=8,
        unique=True,
        null=True,
        blank=True,
        help_text=_("One-time code for Telegram bot registration"),
    )
    qr_token = models.CharField(_("QR token"), max_length=32, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = _("Master")
        verbose_name_plural = _("Masters")
        ordering: ClassVar[list[str]] = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def work_days(self) -> list[int]:
        """Return weekday indices (0=Mon … 6=Sun) when this master works.

        Required by DjangoAvailabilityAdapter. Derived from MasterWorkingDay records.
        """
        return list(self.working_days.values_list("weekday", flat=True))

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.bot_access_code:
            self.bot_access_code = f"LILY{secrets.randbelow(9000) + 1000}"
        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)
