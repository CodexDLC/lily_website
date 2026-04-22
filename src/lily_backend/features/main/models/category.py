from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from codex_django.core.mixins.models import SeoMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class ServiceCategory(SeoMixin, models.Model):
    BENTO_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("hair", _("Friseur & Styling")),
        ("nails", _("Nagelservice")),
        ("face", _("Kosmetologie")),
        ("eyes", _("Brows & Lashes")),
        ("body", _("Massage & Relax")),
        ("hair_removal", _("Depilation")),
    ]

    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), unique=True)
    bento_group = models.CharField(_("bento group"), max_length=20, choices=BENTO_CHOICES, blank=True)
    image = models.ImageField(_("image"), upload_to="categories/", blank=True, null=True)
    icon = models.FileField(_("icon"), upload_to="categories/icons/", blank=True, null=True)
    description = models.TextField(_("description"), blank=True)
    content = models.TextField(_("SEO content"), blank=True)
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_("If unchecked, this category will be hidden from the website entirely."),
    )
    is_planned = models.BooleanField(
        _("coming soon"),
        default=False,
        help_text=_("If checked, shows 'Coming Soon' badge. Used for categories that will be available later."),
    )
    order = models.PositiveIntegerField(_("order"), default=0)

    objects: Manager[ServiceCategory] = models.Manager()

    class Meta:
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")
        ordering: ClassVar[list[str]] = ["order", "name"]

    @property
    def title(self) -> str:
        return self.name

    @property
    def active_masters_count(self) -> int:
        return self.masters.filter(status="active").count()

    @property
    def min_price(self) -> float | None:
        from django.db.models import Min

        return self.services.filter(is_active=True).aggregate(Min("price"))["price__min"]

    def __str__(self) -> str:
        return self.name
