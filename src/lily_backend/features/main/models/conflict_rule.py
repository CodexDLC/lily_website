from typing import ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _


class ServiceConflictRule(models.Model):
    """Cart-level conflict rule between two services.

    Controls what happens when a client adds a service that conflicts
    with one already in their booking cart.

    Note: Service.excludes M2M is used by the booking engine for slot
    overlap detection. This model is UI/cart logic only.
    """

    REPLACES = "replaces"
    EXCLUDES = "excludes"
    RULE_TYPE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (REPLACES, _("Replaces (adds source, removes target from cart)")),
        (EXCLUDES, _("Excludes (cannot be in cart together)")),
    ]

    source = models.ForeignKey(
        "main.Service",
        on_delete=models.CASCADE,
        related_name="conflict_rules_from",
        verbose_name=_("source service"),
    )
    target = models.ForeignKey(
        "main.Service",
        on_delete=models.CASCADE,
        related_name="conflict_rules_to",
        verbose_name=_("target service"),
    )
    rule_type = models.CharField(
        _("rule type"),
        max_length=20,
        choices=RULE_TYPE_CHOICES,
        default=REPLACES,
    )
    is_active = models.BooleanField(_("active"), default=True)
    note = models.CharField(_("admin note"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Service Conflict Rule")
        verbose_name_plural = _("Service Conflict Rules")
        unique_together = [("source", "target", "rule_type")]

    def __str__(self) -> str:
        return f"{self.source} —[{self.rule_type}]→ {self.target}"
