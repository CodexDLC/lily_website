from typing import ClassVar

from codex_django.booking.mixins import AbstractWorkingDay, MasterDayOffMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from .master import Master


class MasterWorkingDay(AbstractWorkingDay):
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name="working_days",
        verbose_name=_("master"),
    )

    class Meta:
        verbose_name = _("Working Day")
        verbose_name_plural = _("Working Days")
        unique_together: ClassVar[list[tuple[str, str]]] = [("master", "weekday")]


class MasterDayOff(MasterDayOffMixin):
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name="days_off",
        verbose_name=_("master"),
    )

    class Meta:
        verbose_name = _("Day Off")
        verbose_name_plural = _("Days Off")
        unique_together: ClassVar[list[tuple[str, str]]] = [("master", "date")]
