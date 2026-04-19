from __future__ import annotations

from typing import ClassVar

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class LoyaltyProfile(models.Model):
    """Cached loyalty state for a registered client profile."""

    profile = models.OneToOneField(
        "system.UserProfile",
        on_delete=models.CASCADE,
        related_name="loyalty",
        verbose_name=_("user profile"),
    )
    level = models.PositiveSmallIntegerField(
        _("level"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        db_index=True,
    )
    best_level = models.PositiveSmallIntegerField(
        _("best level"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        db_index=True,
    )
    progress_percent = models.PositiveSmallIntegerField(
        _("progress percent"),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    effective_spend_score = models.DecimalField(
        _("effective spend score"),
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    behavior_multiplier = models.DecimalField(
        _("behavior multiplier"),
        max_digits=4,
        decimal_places=2,
        default=1,
    )
    source_hash = models.CharField(_("source hash"), max_length=64, blank=True, db_index=True)
    calculated_at = models.DateTimeField(_("calculated at"), null=True, blank=True)
    stats = models.JSONField(_("stats"), default=dict, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Loyalty Profile")
        verbose_name_plural = _("Loyalty Profiles")
        ordering: ClassVar[list[str]] = ["-level", "-effective_spend_score"]

    def __str__(self) -> str:
        return f"{self.profile} - {self.level}/4"
