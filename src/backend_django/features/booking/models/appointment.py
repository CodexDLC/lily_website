"""Appointment model (client booking)."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import TimestampMixin

from .client import Client
from .master import Master


class Appointment(TimestampMixin, models.Model):
    """
    Client booking/appointment with a master for a specific service.
    """

    # === Core Relationships ===
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="appointments", verbose_name=_("Client"))

    master = models.ForeignKey(Master, on_delete=models.PROTECT, related_name="appointments", verbose_name=_("Master"))

    service = models.ForeignKey(
        "main.Service", on_delete=models.PROTECT, related_name="appointments", verbose_name=_("Service")
    )

    # === Scheduling ===
    datetime_start = models.DateTimeField(
        verbose_name=_("Start Date & Time"), db_index=True, help_text=_("Appointment start time")
    )

    duration_minutes = models.PositiveIntegerField(
        verbose_name=_("Duration (minutes)"), help_text=_("Service duration (auto-filled from Service model)")
    )

    # === Pricing (Snapshot) ===
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Price (€)"),
        help_text=_("Price at booking time (snapshot)"),
    )

    # === Status Tracking ===
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_NO_SHOW = "no_show"

    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending Confirmation")),
        (STATUS_CONFIRMED, _("Confirmed")),
        (STATUS_COMPLETED, _("Completed")),
        (STATUS_CANCELLED, _("Cancelled")),
        (STATUS_NO_SHOW, _("No Show")),
    ]

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True, verbose_name=_("Status")
    )

    # === Booking Source ===
    SOURCE_WEBSITE = "website"
    SOURCE_TELEGRAM = "telegram"
    SOURCE_PHONE = "phone"
    SOURCE_ADMIN = "admin"

    SOURCE_CHOICES = [
        (SOURCE_WEBSITE, _("Website")),
        (SOURCE_TELEGRAM, _("Telegram Bot")),
        (SOURCE_PHONE, _("Phone")),
        (SOURCE_ADMIN, _("Admin Panel")),
    ]

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_WEBSITE,
        verbose_name=_("Booking Source"),
        help_text=_("Where this appointment was created"),
    )

    # === Cancellation Info ===
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Cancelled At"))

    CANCEL_REASON_CLIENT = "client"
    CANCEL_REASON_MASTER = "master"
    CANCEL_REASON_RESCHEDULE = "reschedule"
    CANCEL_REASON_OTHER = "other"

    CANCEL_REASON_CHOICES = [
        (CANCEL_REASON_CLIENT, _("Cancelled by Client")),
        (CANCEL_REASON_MASTER, _("Cancelled by Master")),
        (CANCEL_REASON_RESCHEDULE, _("Rescheduled")),
        (CANCEL_REASON_OTHER, _("Other")),
    ]

    cancel_reason = models.CharField(
        max_length=20, choices=CANCEL_REASON_CHOICES, blank=True, verbose_name=_("Cancellation Reason")
    )

    cancel_note = models.TextField(
        blank=True, verbose_name=_("Cancellation Note"), help_text=_("Additional details about cancellation")
    )

    # === Client Notes ===
    client_notes = models.TextField(
        blank=True,
        verbose_name=_("Client Notes"),
        help_text=_("Special requests from client (e.g. allergies, preferences)"),
    )

    # === Admin Notes ===
    admin_notes = models.TextField(
        blank=True, verbose_name=_("Admin Notes"), help_text=_("Internal notes (not visible to client)")
    )

    # === Notifications ===
    reminder_sent = models.BooleanField(
        default=False, verbose_name=_("Reminder Sent"), help_text=_("SMS/Email reminder was sent")
    )

    reminder_sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Reminder Sent At"))

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering = ["-datetime_start"]
        indexes = [
            models.Index(fields=["master", "datetime_start"]),
            models.Index(fields=["client", "datetime_start"]),
            models.Index(fields=["status", "datetime_start"]),
        ]

    def __str__(self):
        return f"{self.client.display_name()} → {self.master.name} ({self.datetime_start.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        """Auto-fill duration and price from service"""
        if not self.duration_minutes:
            self.duration_minutes = self.service.duration
        if not self.price:
            self.price = self.service.price
        super().save(*args, **kwargs)

    def clean(self):
        """Validate no double-booking"""
        if not self.pk:  # Only for new appointments
            conflicts = Appointment.objects.filter(
                master=self.master,
                datetime_start__lt=self.datetime_end,
                datetime_start__gt=self.datetime_start - timedelta(minutes=self.duration_minutes or 60),
                status__in=[self.STATUS_PENDING, self.STATUS_CONFIRMED],
            ).exists()

            if conflicts:
                raise ValidationError({"datetime_start": _("This time slot is already booked.")})

    @property
    def datetime_end(self):
        """Calculate appointment end time"""
        return self.datetime_start + timedelta(minutes=self.duration_minutes)

    @property
    def is_past(self):
        """Check if appointment is in the past"""
        return self.datetime_start < timezone.now()

    @property
    def is_upcoming(self):
        """Check if appointment is in the future"""
        return self.datetime_start > timezone.now()

    @property
    def is_today(self):
        """Check if appointment is today"""
        today = timezone.now().date()
        return self.datetime_start.date() == today

    def can_cancel(self):
        """Check if appointment can be cancelled"""
        if self.status in [self.STATUS_CANCELLED, self.STATUS_COMPLETED]:
            return False
        # Add time restriction (e.g. can't cancel within 2 hours)
        hours_until = (self.datetime_start - timezone.now()).total_seconds() / 3600
        return hours_until >= 2

    def cancel(self, reason=CANCEL_REASON_CLIENT, note=""):
        """Cancel appointment"""
        if not self.can_cancel():
            raise ValidationError(_("This appointment cannot be cancelled."))

        self.status = self.STATUS_CANCELLED
        self.cancelled_at = timezone.now()
        self.cancel_reason = reason
        self.cancel_note = note
        self.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])

    def mark_completed(self):
        """Mark appointment as completed"""
        if self.status != self.STATUS_CONFIRMED:
            raise ValidationError(_("Only confirmed appointments can be marked as completed."))

        self.status = self.STATUS_COMPLETED
        self.save(update_fields=["status", "updated_at"])
