"""Client model (Ghost User pattern)."""

import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import TimestampMixin

User = get_user_model()


class Client(TimestampMixin, models.Model):
    """
    Client profile (salon customer).
    Can exist WITHOUT Django User (ghost) or be linked after activation.
    """

    # === Contact Information ===
    phone = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        verbose_name=_("Phone Number"),
        help_text=_("Primary contact method"),
    )
    email = models.EmailField(
        blank=True,
        db_index=True,
        verbose_name=_("Email"),
        help_text=_("Email for notifications and account activation"),
    )

    first_name = models.CharField(max_length=100, blank=True, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, blank=True, verbose_name=_("Last Name"))

    # === Socials ===
    instagram = models.CharField(
        max_length=100, blank=True, verbose_name=_("Instagram"), help_text=_("Username or link")
    )
    telegram = models.CharField(max_length=100, blank=True, verbose_name=_("Telegram"), help_text=_("Username or link"))

    # === Django User Link (Optional) ===
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_profile",
        verbose_name=_("Django User Account"),
        help_text=_("Linked when client activates account"),
    )

    # === Access Control ===
    access_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        editable=False,
        verbose_name=_("Access Token"),
        help_text=_("Used in SMS/Email links for appointment management"),
    )

    # === Status Tracking ===
    STATUS_GUEST = "guest"
    STATUS_ACTIVE = "active"
    STATUS_BLOCKED = "blocked"

    STATUS_CHOICES = [
        (STATUS_GUEST, _("Guest (Temporary)")),
        (STATUS_ACTIVE, _("Active (Registered)")),
        (STATUS_BLOCKED, _("Blocked")),
    ]

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_GUEST, db_index=True, verbose_name=_("Status")
    )

    # === Marketing ===
    consent_marketing = models.BooleanField(
        default=False,
        verbose_name=_("Marketing Consent"),
        help_text=_("Client agreed to receive promotional materials"),
    )
    consent_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Consent Given Date"))

    # === Admin Notes ===
    notes = models.TextField(
        blank=True, verbose_name=_("Internal Notes"), help_text=_("Admin-only notes about the client")
    )

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "status"]),
            models.Index(fields=["email", "status"]),
        ]
        # Исправлено: используем condition вместо check для совместимости с Django 5.2+
        constraints = [models.CheckConstraint(condition=~models.Q(phone="", email=""), name="client_must_have_contact")]

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.phone or self.email})"
        return self.phone or self.email or f"Client #{self.pk}"

    def save(self, *args, **kwargs):
        """Generate access token on creation"""
        if not self.access_token:
            self.access_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def get_full_name(self):
        """Return full name joined by space"""
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts)

    def display_name(self):
        """Name for public display (hides contact info if no name)"""
        name = self.get_full_name()
        return name if name else _("Guest")

    def activate_account(self, user):
        """Link to Django User and activate account"""
        self.user = user
        self.status = self.STATUS_ACTIVE
        self.save(update_fields=["user", "status", "updated_at"])

    @property
    def is_ghost(self):
        """Check if this is a temporary ghost account"""
        return self.status == self.STATUS_GUEST and self.user is None

    @property
    def primary_contact(self):
        """Return primary contact method"""
        return self.phone or self.email
