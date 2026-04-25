import secrets
from typing import Any, ClassVar

from codex_django.booking.mixins import AbstractBookableAppointment
from django.db import models
from django.utils.translation import gettext_lazy as _

from features.main.models import Service

from .master import Master


class Appointment(AbstractBookableAppointment):
    SOURCE_WEBSITE = "website"
    SOURCE_TELEGRAM = "telegram"
    SOURCE_PHONE = "phone"
    SOURCE_ADMIN = "admin"
    SOURCE_CHOICES: ClassVar[list[tuple[str, Any]]] = [
        (SOURCE_WEBSITE, _("Website")),
        (SOURCE_TELEGRAM, _("Telegram Bot")),
        (SOURCE_PHONE, _("Phone")),
        (SOURCE_ADMIN, _("Admin Panel")),
    ]

    CANCEL_REASON_CLIENT = "client"
    CANCEL_REASON_MASTER = "master"
    CANCEL_REASON_RESCHEDULE = "reschedule"
    CANCEL_REASON_MASTER_BUSY = "master_busy"
    CANCEL_REASON_MASTER_ILL = "master_ill"
    CANCEL_REASON_NO_MATERIALS = "no_materials"
    CANCEL_REASON_BLACKLIST = "client_blacklist"
    CANCEL_REASON_OTHER = "other"
    CANCEL_REASON_CHOICES: ClassVar[list[tuple[str, Any]]] = [
        (CANCEL_REASON_CLIENT, _("Cancelled by Client")),
        (CANCEL_REASON_MASTER, _("Cancelled by Master")),
        (CANCEL_REASON_RESCHEDULE, _("Rescheduled")),
        (CANCEL_REASON_MASTER_BUSY, _("Master is busy")),
        (CANCEL_REASON_MASTER_ILL, _("Master is ill")),
        (CANCEL_REASON_NO_MATERIALS, _("Missing materials")),
        (CANCEL_REASON_BLACKLIST, _("Client in blacklist")),
        (CANCEL_REASON_OTHER, _("Other")),
    ]

    master = models.ForeignKey(Master, on_delete=models.PROTECT, related_name="appointments", verbose_name=_("master"))
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, related_name="appointments", verbose_name=_("service")
    )
    client = models.ForeignKey(
        "system.Client",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="appointments",
        verbose_name=_("client"),
    )
    lang = models.CharField(_("language"), max_length=5, default="de")
    price = models.DecimalField(_("price (€)"), max_digits=10, decimal_places=2, default=0)
    price_actual = models.DecimalField(_("actual price (€)"), max_digits=10, decimal_places=2, null=True, blank=True)
    finalize_token = models.CharField(
        _("finalization token"), max_length=64, unique=True, null=True, blank=True, db_index=True
    )
    source = models.CharField(_("booking source"), max_length=20, choices=SOURCE_CHOICES, default=SOURCE_WEBSITE)
    cancelled_at = models.DateTimeField(_("cancelled at"), null=True, blank=True)
    cancel_reason = models.CharField(_("cancellation reason"), max_length=20, choices=CANCEL_REASON_CHOICES, blank=True)
    cancel_note = models.TextField(_("cancellation note"), blank=True)
    client_notes = models.TextField(_("client notes"), blank=True)
    admin_notes = models.TextField(_("admin notes"), blank=True)
    reminder_sent = models.BooleanField(_("reminder sent"), default=False)
    reminder_sent_at = models.DateTimeField(_("reminder sent at"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    def can_cancel(self) -> bool:
        """Check if the appointment can be cancelled (at least 2 hours before start)."""
        if self.status in [self.STATUS_CANCELLED, self.STATUS_COMPLETED]:
            return False
        from django.utils import timezone

        hours_until = (self.datetime_start - timezone.now()).total_seconds() / 3600
        return hours_until >= 2

    def cancel(self, reason: str = "other", note: str = "") -> None:
        """Cancel the appointment with a reason and optional note."""
        if not self.can_cancel():
            from django.core.exceptions import ValidationError

            raise ValidationError(_("This appointment cannot be cancelled."))

        from django.utils import timezone

        self.status = self.STATUS_CANCELLED
        self.cancelled_at = timezone.now()
        self.cancel_reason = reason
        self.cancel_note = note
        self.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])

        from features.conversations.services.notifications import _get_engine

        _get_engine().dispatch_event("booking.cancelled", self)

    def confirm(self) -> None:
        """Confirm a pending appointment."""
        if self.status != self.STATUS_PENDING:
            from django.core.exceptions import ValidationError

            raise ValidationError(_("Only pending appointments can be confirmed."))
        self.status = self.STATUS_CONFIRMED
        self.save(update_fields=["status", "updated_at"])

        from features.conversations.services.notifications import _get_engine

        _get_engine().dispatch_event("booking.confirmed", self)

    def mark_completed(self) -> None:
        """Mark a confirmed appointment as completed."""
        if self.status != self.STATUS_CONFIRMED:
            from django.core.exceptions import ValidationError

            raise ValidationError(_("Only confirmed appointments can be completed."))
        self.status = self.STATUS_COMPLETED
        self.save(update_fields=["status", "updated_at"])

    def mark_no_show(self) -> None:
        """Mark appointment as no-show."""
        self.status = self.STATUS_NO_SHOW
        self.save(update_fields=["status", "updated_at"])

        from features.conversations.services.notifications import _get_engine

        _get_engine().dispatch_event("booking.no_show", self)

    def propose_reschedule(self) -> None:
        """Set status to reschedule proposed."""
        self.status = self.STATUS_RESCHEDULE_PROPOSED
        self.save(update_fields=["status", "updated_at"])

        from features.conversations.services.notifications import _get_engine

        _get_engine().dispatch_event("booking.rescheduled", self)

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering: ClassVar[list[str]] = ["-datetime_start"]
        indexes = [
            models.Index(fields=["master", "datetime_start"]),
            models.Index(fields=["status", "datetime_start"]),
        ]

    def __str__(self) -> str:
        return f"{self.client} → {self.master} ({self.datetime_start})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.finalize_token:
            self.finalize_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
