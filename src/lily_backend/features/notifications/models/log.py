from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationLog(models.Model):
    """Log of system notifications sent to administrators."""

    event_type = models.CharField(_("event type"), max_length=100)
    channel = models.CharField(_("channel"), max_length=20)
    recipient = models.CharField(_("recipient"), max_length=255)
    status = models.CharField(_("status"), max_length=20, choices=[("success", _("Success")), ("failed", _("Failed"))])
    subject = models.CharField(_("subject"), max_length=255, blank=True)
    error_message = models.TextField(_("error message"), blank=True)
    context_preview = models.JSONField(_("context preview"), default=dict, blank=True)
    sent_at = models.DateTimeField(_("sent at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Notification Log")
        verbose_name_plural = _("Notification Logs")
        ordering = ["-sent_at"]

    def __str__(self) -> str:
        return f"[{self.status.upper()}] {self.event_type} -> {self.recipient}"
