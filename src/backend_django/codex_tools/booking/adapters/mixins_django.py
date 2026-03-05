"""
codexn_tools.booking.adapters.mixins_django
=============================================
Опциональные Django-миксины для стандартизации моделей
под требования движка бронирования.

Требует: Django (pip install codexn_tools[django])

Применение к модели Master:
    from codexn_tools.booking.adapters.mixins_django import BookableMasterMixin

    class Master(BookableMasterMixin, TimestampMixin, models.Model):
        name = models.CharField(...)
        # BookableMasterMixin добавит поля ниже автоматически

Применение к модели Service:
    from codexn_tools.booking.adapters.mixins_django import BookableServiceMixin

    class Service(BookableServiceMixin, TimestampMixin, models.Model):
        title = models.CharField(...)
        # BookableServiceMixin добавит min_gap_after_minutes

ВАЖНО: поля с null=True — если не заданы на конкретном экземпляре,
DjangoAvailabilityAdapter автоматически берёт дефолты из BookingSettings.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class BookableMasterMixin(models.Model):
    """
    Миксин для модели исполнителя (мастер, специалист, ресурс).

    Добавляет поля необходимые движку для корректного расчёта слотов.
    Все поля nullable — если не заданы, адаптер использует глобальные
    дефолты из BookingSettings.

    Логика приоритетов (в DjangoAvailabilityAdapter):
        master.work_start не None  → используем его
        master.work_start is None  → берём BookingSettings.default_work_start_weekdays

    Поля:
        work_start (TimeField, nullable):
            Начало рабочего дня мастера. Переопределяет глобальное расписание салона.

        work_end (TimeField, nullable):
            Конец рабочего дня мастера.

        break_start (TimeField, nullable):
            Начало перерыва (обед и т.п.). None = нет перерыва.

        break_end (TimeField, nullable):
            Конец перерыва.

        buffer_between_minutes (PositiveIntegerField, nullable):
            Время в минутах между клиентами. Мастеру нужно это время
            для подготовки к следующему клиенту (уборка, инструменты).
            None → BookingSettings.default_buffer_between_minutes.

        min_advance_minutes (PositiveIntegerField, nullable):
            Минимум за сколько минут до начала можно записаться.
            None → BookingSettings.default_min_advance_minutes.

        max_advance_days (PositiveIntegerField, nullable):
            Горизонт записи в днях. Нельзя записаться дальше чем через N дней.
            None → BookingSettings.default_max_advance_days.

    Пример использования в кабинете:
        - Мастер А работает 9:00-18:00, без индивидуальных настроек → берём из салона
        - Мастер Б работает 12:00-20:00 → задаём work_start=12:00, work_end=20:00
        - Мастер В берёт 15 мин перерыв между клиентами → buffer_between_minutes=15
    """

    # Индивидуальный рабочий день (override SiteSettings глобального расписания)
    work_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Work Start"),
        help_text=_("Individual work start time. If empty, uses salon schedule."),
    )
    work_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Work End"),
        help_text=_("Individual work end time. If empty, uses salon schedule."),
    )

    # Перерыв (обед, личное время)
    break_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Break Start"),
        help_text=_("Break start time (lunch etc). Leave empty if no break."),
    )
    break_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Break End"),
        help_text=_("Break end time."),
    )

    # Буферы и горизонт записи
    buffer_between_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Buffer Between Clients (min)"),
        help_text=_(
            "Minutes needed between clients for preparation. If empty, uses global default from Booking Settings."
        ),
    )
    min_advance_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Min Advance Booking (min)"),
        help_text=_("Minimum minutes before appointment start a booking can be made. If empty, uses global default."),
    )
    max_advance_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Max Advance Booking (days)"),
        help_text=_("How many days in advance a booking can be made. If empty, uses global default."),
    )

    max_clients_parallel = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Max Parallel Clients"),
        help_text=_(
            "How many clients this master can serve simultaneously. "
            "1 = one at a time (default). "
            "2+ = group booking support (e.g. couples pedicure). "
            "Used with BookingEngineRequest.group_size."
        ),
    )

    class Meta:
        abstract = True


class BookableServiceMixin(models.Model):
    """
    Миксин для модели услуги.

    Добавляет поля для корректного расчёта цепочек в ChainFinder.

    Поля:
        min_gap_after_minutes (PositiveIntegerField, default=0):
            Минимальная пауза в минутах ПОСЛЕ этой услуги
            перед следующей в цепочке.

            Примеры:
                - Маникюр → Педикюр: min_gap_after_minutes=0 (сразу переходим)
                - Покраска → Стрижка: min_gap_after_minutes=30 (ждём 30 мин)
                - База → Верхнее покрытие: min_gap_after_minutes=15 (сушка)

            ChainFinder учитывает это поле при поиске следующего слота:
            next_service.start >= current_service.end + min_gap_after_minutes

        parallel_ok (BooleanField, default=True):
            Может ли эта услуга выполняться параллельно с другими услугами
            в одной цепочке (разными мастерами одновременно).
            True  → маникюр + педикюр одновременно — ОК.
            False → услуга требует последовательного выполнения
                    (например, после предыдущей: сушка → верхнее покрытие).
            DjangoAvailabilityAdapter читает это поле и передаёт в ServiceRequest.parallel_group.

    Пример применения:
        class Service(BookableServiceMixin, models.Model):
            title = CharField(...)
            duration = PositiveIntegerField(...)
            # + min_gap_after_minutes, parallel_ok добавлены миксином
    """

    min_gap_after_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Gap After Service (min)"),
        help_text=_(
            "Minimum pause in minutes after this service before the next one "
            "in a chain booking (e.g. drying time, waiting). Default: 0."
        ),
    )
    parallel_ok = models.BooleanField(
        default=True,
        verbose_name=_("Can Run in Parallel"),
        help_text=_(
            "Whether this service can be performed simultaneously with other services "
            "in a chain booking (by different masters). "
            "True = manicure + pedicure at the same time is OK. "
            "False = must be strictly sequential."
        ),
    )

    class Meta:
        abstract = True
