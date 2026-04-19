"""Booking Settings model — global booking configuration (singleton)."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import TimestampMixin


class BookingSettings(TimestampMixin, models.Model):
    """
    Глобальные настройки системы бронирования. Singleton (один ряд в таблице).

    Используются как ДЕФОЛТЫ когда у мастера нет индивидуальных настроек
    (поля из BookableMasterMixin). Редактируется в кабинете → "Настройки букинга".

    Логика применения (в DjangoAvailabilityAdapter):
        master.work_start не None → используем его
        master.work_start is None → берём из BookingSettings (этот класс)

    Рабочие часы салона хранятся в SiteSettings (глобальное расписание).
    Этот класс хранит booking-специфичные настройки (шаг, буферы, ограничения).
    """

    # --- Шаг сетки слотов ---
    default_step_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Slot Step (min)"),
        help_text=_("Grid step in minutes for slot generation (e.g. 30 = slots at :00 and :30)."),
    )

    # --- Ограничения записи ---
    default_min_advance_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name=_("Min Advance Booking (min)"),
        help_text=_(
            "Global minimum: booking must be made at least N minutes before appointment. Can be overridden per master."
        ),
    )
    default_max_advance_days = models.PositiveIntegerField(
        default=60,
        verbose_name=_("Max Advance Booking (days)"),
        help_text=_("Global maximum: booking cannot be made more than N days ahead. Can be overridden per master."),
    )

    # --- Буфер между клиентами ---
    default_buffer_between_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Buffer Between Clients (min)"),
        help_text=_(
            "Global default: minutes a master needs between clients for preparation. "
            "0 = no buffer. Can be overridden per master."
        ),
    )

    class Meta:
        verbose_name = _("Booking Settings")
        verbose_name_plural = _("Booking Settings")

    def __str__(self) -> str:
        return "Booking Settings"

    @classmethod
    def load(cls) -> "BookingSettings":
        """
        Singleton-паттерн. Возвращает единственный экземпляр настроек.
        Создаёт с дефолтами если не существует.

        Использование:
            settings = BookingSettings.load()
            step = settings.default_step_minutes  # 30
        """
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
