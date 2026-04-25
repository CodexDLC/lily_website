from typing import ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationRecipient(models.Model):
    """Configuration for who receives admin/staff notifications."""

    KIND_ADMIN = "admin"
    KIND_MANAGER = "manager"

    KIND_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (KIND_ADMIN, _("Administrator")),
        (KIND_MANAGER, _("Manager")),
    ]

    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(_("name"), max_length=150, blank=True)
    kind = models.CharField(_("role/kind"), max_length=20, choices=KIND_CHOICES, default=KIND_ADMIN)
    enabled = models.BooleanField(_("enabled"), default=True)
    note = models.TextField(_("internal note"), blank=True, default="")

    class Meta:
        verbose_name = _("Notification Recipient")
        verbose_name_plural = _("Notification Recipients")
        ordering = ["email"]

    def __str__(self) -> str:
        return f"{self.name or self.email} ({self.get_kind_display()})"
