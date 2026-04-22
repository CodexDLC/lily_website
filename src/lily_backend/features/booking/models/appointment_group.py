import secrets
from typing import Any, ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _


class AppointmentGroup(models.Model):
    """A group of appointments created together in a single same-day booking.

    Created ONLY when a client books 2+ services on the same day.
    Single-service bookings and multi-day bookings do NOT create a group —
    those remain as independent Appointment records.
    """

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_CONFIRMED, _("Confirmed")),
        (STATUS_CANCELLED, _("Cancelled")),
    ]

    SOURCE_WEBSITE = "website"
    SOURCE_ADMIN = "admin"
    SOURCE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (SOURCE_WEBSITE, _("Website")),
        (SOURCE_ADMIN, _("Admin Panel")),
    ]

    client = models.ForeignKey(
        "system.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment_groups",
        verbose_name=_("client"),
    )
    group_token = models.CharField(
        _("group token"),
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("Used in the success page URL. Auto-generated on save."),
    )
    mode = models.CharField(
        _("mode"),
        max_length=20,
        choices=[("same_day", _("Same Day"))],
        default="same_day",
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    source = models.CharField(
        _("booking source"),
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_WEBSITE,
    )
    combo = models.ForeignKey(
        "main.ServiceCombo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment_groups",
        verbose_name=_("applied combo/promo"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Appointment Group")
        verbose_name_plural = _("Appointment Groups")
        ordering: ClassVar[list[str]] = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        client_str = str(self.client) if self.client else "—"
        return f"Group #{self.pk} / {client_str} ({self.get_status_display()})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.group_token:
            self.group_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def confirm_all(self) -> None:
        """Confirm all appointments in the group."""
        from django.db import transaction

        with transaction.atomic():
            for item in self.items.select_related("appointment"):
                appt = item.appointment
                if appt.status == appt.STATUS_PENDING:
                    appt.confirm()
            self.status = self.STATUS_CONFIRMED
            self.save(update_fields=["status", "updated_at"])

    def cancel_all(self, reason: str = "other", note: str = "") -> None:
        """Cancel all appointments in the group."""
        from django.db import transaction

        with transaction.atomic():
            for item in self.items.select_related("appointment"):
                appt = item.appointment
                if appt.status not in [appt.STATUS_CANCELLED, appt.STATUS_COMPLETED]:
                    appt.status = appt.STATUS_CANCELLED
                    appt.cancel_reason = reason
                    appt.cancel_note = note
                    appt.save(update_fields=["status", "cancel_reason", "cancel_note", "updated_at"])
            self.status = self.STATUS_CANCELLED
            self.save(update_fields=["status", "updated_at"])


class AppointmentGroupItem(models.Model):
    """Junction between AppointmentGroup and individual Appointment records."""

    group = models.ForeignKey(
        AppointmentGroup,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("group"),
    )
    appointment = models.OneToOneField(
        "booking.Appointment",
        on_delete=models.CASCADE,
        related_name="group_item",
        verbose_name=_("appointment"),
    )
    order = models.PositiveSmallIntegerField(_("order in chain"), default=0)

    class Meta:
        verbose_name = _("Group Item")
        verbose_name_plural = _("Group Items")
        ordering: ClassVar[list[str]] = ["order"]
        unique_together = [("group", "order")]

    def __str__(self) -> str:
        return f"{self.group} / item {self.order}"
