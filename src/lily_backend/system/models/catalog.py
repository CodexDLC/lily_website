from django.db import models
from django.utils.translation import gettext_lazy as _


class CatalogImportState(models.Model):
    key = models.CharField(_("catalog key"), max_length=100, unique=True, db_index=True)
    source_hash = models.CharField(_("source hash"), max_length=64)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Catalog import state")
        verbose_name_plural = _("Catalog import states")

    def __str__(self) -> str:
        return f"{self.key}: {self.source_hash[:12]}"
