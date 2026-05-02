from typing import ClassVar

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ServiceCombo(models.Model):
    """A promotional combo set of services with a discount.

    Used for future pricing/promo logic — separate from ServiceConflictRule
    which handles cart replacement logic.
    """

    PERCENT = "percent"
    FIXED = "fixed"
    FIXED_PRICE = "fixed_price"
    DISCOUNT_TYPE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (PERCENT, _("Percent discount (e.g. -10%)")),
        (FIXED, _("Fixed discount (e.g. -5€)")),
        (FIXED_PRICE, _("Fixed combo price")),
    ]

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), unique=True)
    description = models.TextField(_("description"), blank=True)
    promo_title = models.CharField(_("promo title"), max_length=200, blank=True)
    promo_text = models.TextField(_("promo text"), blank=True)
    promo_image = models.ImageField(_("promo image"), upload_to="combos/", blank=True, null=True)
    promo_button_text = models.CharField(_("promo button text"), max_length=80, default=_("Termin buchen"))
    show_on_home = models.BooleanField(_("show on home page"), default=True)
    is_featured = models.BooleanField(_("featured promo"), default=False)
    promo_order = models.PositiveIntegerField(_("promo order"), default=0)
    discount_type = models.CharField(
        _("discount type"),
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default=PERCENT,
    )
    discount_value = models.DecimalField(
        _("discount value"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Percent (10 = 10%) or fixed amount in euros."),
    )
    is_active = models.BooleanField(_("active"), default=True)
    valid_from = models.DateField(_("valid from"), null=True, blank=True)
    valid_until = models.DateField(_("valid until"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Service Combo")
        verbose_name_plural = _("Service Combos")
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def display_title(self) -> str:
        return self.promo_title or self.name

    @property
    def display_text(self) -> str:
        return self.promo_text or self.description

    @property
    def booking_url(self) -> str:
        return f"{reverse('booking:booking_wizard')}?combo={self.slug}"

    @property
    def is_available_now(self) -> bool:
        today = timezone.localdate()
        if not self.is_active:
            return False
        if self.valid_from and self.valid_from > today:
            return False
        return not (self.valid_until and self.valid_until < today)


class ServiceComboItem(models.Model):
    """A single service within a combo set."""

    combo = models.ForeignKey(
        ServiceCombo,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("combo"),
    )
    service = models.ForeignKey(
        "main.Service",
        on_delete=models.CASCADE,
        related_name="combo_items",
        verbose_name=_("service"),
    )
    is_required = models.BooleanField(
        _("required"),
        default=True,
        help_text=_("If false, this service is optional within the combo."),
    )
    order = models.PositiveSmallIntegerField(_("order"), default=0)

    class Meta:
        verbose_name = _("Combo Item")
        verbose_name_plural = _("Combo Items")
        ordering: ClassVar[list[str]] = ["order"]
        unique_together = [("combo", "service")]

    def __str__(self) -> str:
        return f"{self.combo.name} / {self.service.name}"
