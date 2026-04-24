import uuid
from typing import Any, ClassVar

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
    """
    Client (Customer) model.
    Holds data obtained during interaction (booking, forms).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_profile",
        verbose_name=_("user"),
    )

    # Interaction data (available for Ghost clients)
    first_name = models.CharField(_("first name"), max_length=255, blank=True)
    last_name = models.CharField(_("last name"), max_length=255, blank=True)
    patronymic = models.CharField(_("patronymic"), max_length=255, blank=True)
    phone = models.CharField(_("phone"), max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(_("email"), unique=True, null=True, blank=True)

    # Consents obtained during interaction
    consent_marketing = models.BooleanField(_("marketing consent"), default=False)
    consent_analytics = models.BooleanField(_("analytics consent"), default=False)
    consent_date = models.DateTimeField(_("consent date"), null=True, blank=True)

    is_ghost = models.BooleanField(
        _("is ghost"),
        default=True,
        help_text=_("True if the client was created by staff and hasn't registered/linked an account yet."),
    )

    STATUS_GUEST = "guest"
    STATUS_ACTIVE = "active"
    STATUS_BLOCKED = "blocked"
    STATUS_CHOICES = [
        (STATUS_GUEST, _("Guest")),
        (STATUS_ACTIVE, _("Active")),
        (STATUS_BLOCKED, _("Blocked")),
    ]
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_GUEST,
        db_index=True,
    )

    access_token = models.CharField(
        _("access token"),
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    unsubscribe_token = models.UUIDField(
        _("unsubscribe token"),
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    email_opt_out_at = models.DateTimeField(_("email opt-out at"), null=True, blank=True)

    note = models.TextField(_("internal note"), blank=True)

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.phone or self.email or f"Client #{self.pk}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.access_token:
            self.access_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
