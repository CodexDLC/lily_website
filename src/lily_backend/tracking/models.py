from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class PageView(models.Model):
    """Aggregated daily page view counts flushed from Redis."""

    path = models.CharField(_("path"), max_length=500, db_index=True)
    date = models.DateField(_("date"), db_index=True)
    views = models.PositiveIntegerField(_("views"), default=0)

    class Meta:
        verbose_name = _("Page view")
        verbose_name_plural = _("Page views")
        unique_together = ("path", "date")
        ordering = ["-date", "-views"]

    def __str__(self) -> str:
        return f"{self.date} {self.path} — {self.views}"
