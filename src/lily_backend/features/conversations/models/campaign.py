from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Campaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        QUEUED = "queued", _("Queued")
        SENDING = "sending", _("Sending")
        DONE = "done", _("Done")
        FAILED = "failed", _("Failed")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns_created",
        verbose_name=_("created by"),
    )

    subject = models.CharField(_("subject"), max_length=500)
    body_text = models.TextField(_("body text"))
    is_marketing = models.BooleanField(
        _("is marketing"),
        default=True,
        help_text=_("If unchecked, marketing consent will be ignored (use for critical updates)."),
    )
    template_key = models.CharField(_("template key"), max_length=64, default="basic")

    locale = models.CharField(_("locale"), max_length=10, default="de", db_index=True)
    body_translations = models.JSONField(_("body translations"), default=dict, blank=True)

    audience_filter = models.JSONField(_("audience filter"), default=dict, blank=True)

    status = models.CharField(
        _("status"),
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    status_reason = models.TextField(_("status reason"), blank=True)

    send_at = models.DateTimeField(_("send at"), null=True, blank=True)
    sent_at = models.DateTimeField(_("sent at"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    arq_parent_job_id = models.CharField(_("arq parent job id"), max_length=128, blank=True)

    class Meta:
        verbose_name = _("Email Campaign")
        verbose_name_plural = _("Email Campaigns")
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.get_status_display()}] {self.subject}"


class CampaignRecipient(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")
        BOUNCED = "bounced", _("Bounced")
        UNSUBSCRIBED = "unsubscribed", _("Unsubscribed")

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name=_("campaign"),
    )
    recipient = models.ForeignKey(
        settings.CONVERSATIONS_RECIPIENT_MODEL,
        on_delete=models.CASCADE,
        related_name="campaign_entries",
        verbose_name=_("recipient"),
    )

    email = models.EmailField(_("email"))
    first_name = models.CharField(_("first name"), max_length=255, blank=True)
    last_name = models.CharField(_("last name"), max_length=255, blank=True)
    locale = models.CharField(_("locale"), max_length=10, default="de")

    status = models.CharField(
        _("status"),
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    arq_job_id = models.CharField(_("arq job id"), max_length=128, blank=True)
    sent_at = models.DateTimeField(_("sent at"), null=True, blank=True)
    error = models.TextField(_("error"), blank=True)

    class Meta:
        verbose_name = _("Campaign Recipient")
        verbose_name_plural = _("Campaign Recipients")
        unique_together: ClassVar = [("campaign", "recipient")]
        indexes: ClassVar = [
            models.Index(fields=["campaign", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.email} → {self.campaign}"
