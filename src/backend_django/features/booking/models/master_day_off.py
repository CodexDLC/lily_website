from django.db import models
from django.utils.translation import gettext_lazy as _
from features.booking.models.master import Master


class MasterDayOff(models.Model):
    """
    Model to store specific days off for a master.
    Existing appointments on these days remain active, but new slots are hidden.
    """

    master = models.ForeignKey(Master, on_delete=models.CASCADE, related_name="days_off")
    date = models.DateField(_("Date"))
    reason = models.CharField(_("Reason"), max_length=255, blank=True)

    class Meta:
        unique_together = ["master", "date"]
        verbose_name = _("Master Day Off")
        verbose_name_plural = _("Master Days Off")
        ordering = ["date"]

    def __str__(self):
        return f"{self.master} - {self.date}"
