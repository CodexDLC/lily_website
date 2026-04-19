from django.db import models
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import TimestampMixin


class ContactRequest(TimestampMixin, models.Model):
    """
    Contact form submission linked to a Client.
    """

    TOPIC_GENERAL = "general"
    TOPIC_BOOKING = "booking"
    TOPIC_JOB = "job"
    TOPIC_OTHER = "other"

    TOPIC_CHOICES = [
        (TOPIC_GENERAL, _("General Question")),
        (TOPIC_BOOKING, _("Questions about Booking")),
        (TOPIC_JOB, _("Job / Career")),
        (TOPIC_OTHER, _("Other")),
    ]

    client = models.ForeignKey(
        "booking.Client", on_delete=models.CASCADE, related_name="contact_requests", verbose_name=_("Client")
    )

    topic = models.CharField(_("Topic"), max_length=50, choices=TOPIC_CHOICES, default=TOPIC_GENERAL)
    message = models.TextField(_("Message"), blank=True)

    is_processed = models.BooleanField(_("Processed"), default=False)
    admin_notes = models.TextField(_("Admin Notes"), blank=True)

    class Meta:
        verbose_name = _("Contact Request")
        verbose_name_plural = _("Contact Requests")
        ordering = ["-created_at"]

    def __str__(self):
        # We can't access self.client.name easily if it's lazy loaded in __str__ sometimes,
        # but usually it works fine. To be safe, we can use pk or try/except.
        # But for admin display, Django handles it.
        return f"Request #{self.pk} - {self.get_topic_display()}"
