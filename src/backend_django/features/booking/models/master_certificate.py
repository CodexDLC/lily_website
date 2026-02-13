"""Master certificates and diplomas model."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import TimestampMixin
from features.system.services.images import optimize_image

from .master import Master


class MasterCertificate(TimestampMixin, models.Model):
    """
    Master's certificates, diplomas, awards.
    Displayed in horizontal carousel on master detail page.
    """

    master = models.ForeignKey(Master, on_delete=models.CASCADE, related_name="certificates", verbose_name=_("Master"))

    # === Certificate Info ===
    title = models.CharField(
        max_length=255, verbose_name=_("Certificate Title"), help_text=_("e.g. 'Advanced Nail Art Course'")
    )

    issuer = models.CharField(
        max_length=255, blank=True, verbose_name=_("Issuing Organization"), help_text=_("e.g. 'German Beauty Academy'")
    )

    issue_date = models.DateField(null=True, blank=True, verbose_name=_("Issue Date"))

    # === Image ===
    image = models.ImageField(
        upload_to="certificates/",
        verbose_name=_("Certificate Image"),
        help_text=_("Scan or photo of certificate (recommended: 1200x900px)"),
    )

    # === Display ===
    order = models.PositiveIntegerField(
        default=0, verbose_name=_("Display Order"), help_text=_("Lower numbers appear first")
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Active"), help_text=_("Show on master page"))

    class Meta:
        verbose_name = _("Master Certificate")
        verbose_name_plural = _("Master Certificates")
        ordering = ["master", "order", "-issue_date"]

    def __str__(self):
        return f"{self.master.name} - {self.title}"

    def save(self, *args, **kwargs):
        if self.image:
            optimize_image(self.image, max_width=1200)
        super().save(*args, **kwargs)
