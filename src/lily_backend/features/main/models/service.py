from typing import ClassVar

from codex_django.booking.mixins import AbstractBookableService
from codex_django.core.mixins.models import SeoMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from .category import ServiceCategory


class Service(SeoMixin, AbstractBookableService):
    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), unique=True)
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("category"),
    )
    masters = models.ManyToManyField(
        "booking.Master",
        blank=True,
        related_name="services",
        verbose_name=_("masters"),
    )
    price = models.DecimalField(_("price (€)"), max_digits=10, decimal_places=2, default=0)
    price_info = models.CharField(_("price display text"), max_length=100, blank=True)
    # duration inherited from AbstractBookableService
    duration_info = models.CharField(_("duration display text"), max_length=100, blank=True)
    description = models.TextField(_("short description"), blank=True)
    content = models.TextField(_("full content"), blank=True)
    image = models.ImageField(_("image"), upload_to="services/", blank=True, null=True)
    is_active = models.BooleanField(_("active"), default=True, db_index=True)
    is_hit = models.BooleanField(_("popular / hit"), default=False)
    is_addon = models.BooleanField(_("is add-on"), default=False)
    order = models.PositiveIntegerField(_("order"), default=0)
    excludes = models.ManyToManyField("self", symmetrical=True, blank=True, verbose_name=_("excludes services"))

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering: ClassVar[list[str]] = ["order", "name"]

    @property
    def title(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name
