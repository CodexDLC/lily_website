"""Scaffold-owned engine gateway for resource-slot booking."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from codex_django.booking.adapters.availability import DjangoAvailabilityAdapter
from codex_django.booking.adapters.cache import BookingCacheAdapter
from codex_django.booking.contracts import BookingEngineGateway
from codex_django.booking.selectors import (
    create_booking as runtime_create_booking,
)
from codex_django.booking.selectors import (
    get_available_slots as runtime_get_available_slots,
)
from codex_django.booking.selectors import (
    get_calendar_data as runtime_get_calendar_data,
)
from codex_django.booking.selectors import (
    get_nearest_slots as runtime_get_nearest_slots,
)

from ..persistence import LilyBookingPersistenceHook, build_single_service_extra_fields
from ..providers.runtime import get_booking_project_data_provider

logger = logging.getLogger(__name__)

MULTI_SERVICE_MAX_UNIQUE_STARTS = 100
MULTI_SERVICE_MAX_SOLUTIONS = 1000
DAY_NAMES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def _day_bounds(target_date: date) -> tuple[datetime, datetime]:
    from django.utils import timezone

    start = timezone.make_aware(datetime.combine(target_date, time.min))
    return start, start + timedelta(days=1)


def _get_settings_day_schedule(settings: Any, weekday: int) -> tuple[time, time] | None:
    """Return Lily salon hours for a weekday from BookingSettings only."""
    day_name = DAY_NAMES[weekday]
    if getattr(settings, f"{day_name}_is_closed", False):
        return None
    start_time = getattr(settings, f"work_start_{day_name}", None)
    end_time = getattr(settings, f"work_end_{day_name}", None)
    if not start_time or not end_time:
        return None
    return start_time, end_time


class EmptyAvailableSlots:
    """Fallback result for days with no available resources."""

    def to_dict(self) -> dict:
        return {"slots": [], "metadata": {}}

    def get_unique_start_times(self) -> list[str]:
        return []


class LoadAwareDjangoAvailabilityAdapter(DjangoAvailabilityAdapter):
    """Availability adapter with project-specific resource prioritization."""

    def __init__(self, *args: Any, load_strategy: str, target_date: date, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._load_strategy = load_strategy
        self._target_date = target_date

    def prioritize_resource_ids(
        self,
        *,
        resource_ids: list[str],
        service: Any,
        target_date: date,
        service_id: int,
    ) -> list[str]:
        del service, service_id
        from ..booking_settings import BookingSettings

        if not resource_ids:
            return resource_ids

        if self._load_strategy == BookingSettings.STRATEGY_EVEN_LOAD:
            return self._sort_by_load(resource_ids, target_date)
        return self._sort_by_priority(resource_ids)

    def _sort_by_priority(self, resource_ids: list[str]) -> list[str]:
        priority_map: dict[int, int] = dict(
            self.resource_model.objects.filter(pk__in=[int(i) for i in resource_ids]).values_list(
                "id", "booking_priority"
            )
        )
        return sorted(resource_ids, key=lambda i: priority_map.get(int(i), 100))

    def _sort_by_load(self, resource_ids: list[str], target_date: date) -> list[str]:
        from django.db.models import Count

        day_start, day_end = _day_bounds(target_date)
        counts: dict[int, int] = dict(
            self.appointment_model.objects.filter(
                master_id__in=[int(i) for i in resource_ids],
                datetime_start__gte=day_start,
                datetime_start__lt=day_end,
                status__in=["pending", "confirmed", "reschedule_proposed"],
            )
            .values("master_id")
            .annotate(cnt=Count("id"))
            .values_list("master_id", "cnt")
        )
        return sorted(resource_ids, key=lambda i: counts.get(int(i), 0))


class LilyBookingAvailabilityAdapter(LoadAwareDjangoAvailabilityAdapter):
    """Lily availability adapter.

    In Lily, BookingSettings owns working hours. MasterWorkingDay only marks
    whether a master works on a weekday.
    """

    def _get_booking_settings(self) -> Any:
        if self._booking_settings is None:
            load = getattr(self.booking_settings_model, "load", None)
            self._booking_settings = load() if callable(load) else self.booking_settings_model.objects.first()
        return self._booking_settings

    def get_working_hours(self, master: Any, target_date: date) -> tuple[datetime, datetime] | None:
        weekday = target_date.weekday()
        if not self.working_day_model.objects.filter(master_id=master.pk, weekday=weekday).exists():
            return None

        schedule = _get_settings_day_schedule(self._get_booking_settings(), weekday)
        if schedule is None:
            return None

        start_time, end_time = schedule
        tz = self._get_tz(master)
        work_start_dt = datetime.combine(target_date, start_time, tzinfo=tz)
        work_end_dt = datetime.combine(target_date, end_time, tzinfo=tz)
        return work_start_dt.astimezone(UTC), work_end_dt.astimezone(UTC)

    def get_break_interval(self, master: Any, target_date: date) -> None:
        del master, target_date
        return None


class BookingRuntimeEngineGateway(BookingEngineGateway):
    """Feature-facing engine gateway."""

    def __init__(self, provider: Any = None) -> None:
        self.provider = provider or get_booking_project_data_provider()

    def _build_adapter(self, target_date: date | None = None) -> DjangoAvailabilityAdapter:
        from ..booking_settings import BookingSettings

        feature_models = self.provider.get_feature_models()
        strategy = BookingSettings.load().load_strategy
        return LilyBookingAvailabilityAdapter(
            resource_model=feature_models.resource_model,
            appointment_model=feature_models.appointment_model,
            service_model=feature_models.service_model,
            working_day_model=feature_models.working_day_model,
            day_off_model=feature_models.day_off_model,
            booking_settings_model=feature_models.booking_settings_model,
            timezone="UTC",
            load_strategy=strategy,
            target_date=target_date or date.today(),
        )

    def get_calendar_data(
        self,
        *,
        year: int,
        month: int,
        today: date | None = None,
        selected_date: date | None = None,
    ) -> list[dict[str, Any]]:
        return runtime_get_calendar_data(year=year, month=month, today=today, selected_date=selected_date)

    def get_available_slots(self, *, service_ids: list[int], target_date: date, **kwargs: Any) -> Any:
        from datetime import date as dt_date

        from ..booking_settings import BookingSettings

        audience = str(kwargs.pop("audience", "public"))
        settings = BookingSettings.load()
        if audience == "public" and settings.book_only_from_next_day and target_date <= dt_date.today():
            return []

        effective_kwargs = {key: value for key, value in kwargs.items() if value is not None}
        if len(service_ids) > 1:
            effective_kwargs.setdefault("max_unique_starts", MULTI_SERVICE_MAX_UNIQUE_STARTS)
            effective_kwargs.setdefault("max_solutions", MULTI_SERVICE_MAX_SOLUTIONS)

        adapter = self._build_adapter(target_date=target_date)
        try:
            return runtime_get_available_slots(adapter, service_ids, target_date, **effective_kwargs)
        except Exception as exc:
            logger.debug("Booking get_available_slots fallback to empty payload: {}", exc)
            return EmptyAvailableSlots()

    def get_nearest_slots(self, *, service_ids: list[int], search_from: date, **kwargs: Any) -> Any:
        from datetime import date as dt_date

        from ..booking_settings import BookingSettings

        audience = str(kwargs.pop("audience", "public"))
        settings = BookingSettings.load()
        effective_search_from = search_from
        if audience == "public" and settings.book_only_from_next_day and search_from <= dt_date.today():
            effective_search_from = dt_date.today() + timedelta(days=1)

        effective_kwargs = {key: value for key, value in kwargs.items() if value is not None}
        adapter = self._build_adapter(target_date=effective_search_from)
        return runtime_get_nearest_slots(adapter, service_ids, effective_search_from, **effective_kwargs)

    def get_resource_day_slots(
        self,
        *,
        resource_id: int,
        target_date: date,
        audience: str = "public",
    ) -> list[str]:
        from django.utils import timezone

        from ..booking_settings import BookingSettings
        from ..models import Appointment, MasterDayOff, MasterWorkingDay

        settings = BookingSettings.load()
        if audience == "public" and settings.book_only_from_next_day and target_date <= date.today():
            return []

        if MasterDayOff.objects.filter(master_id=resource_id, date=target_date).exists():
            return []

        weekday = target_date.weekday()
        if not MasterWorkingDay.objects.filter(master_id=resource_id, weekday=weekday).exists():
            return []

        schedule = _get_settings_day_schedule(settings, weekday)
        if schedule is None:
            return []
        start_time, end_time = schedule

        step = timedelta(minutes=settings.step_minutes or 30)
        window_start = timezone.make_aware(datetime.combine(target_date, start_time))
        window_end = timezone.make_aware(datetime.combine(target_date, end_time))
        day_start, day_end = _day_bounds(target_date)
        busy_ranges = [
            (appt.datetime_start, appt.datetime_start + timedelta(minutes=appt.duration_minutes))
            for appt in Appointment.objects.filter(
                master_id=resource_id,
                datetime_start__gte=day_start,
                datetime_start__lt=day_end,
                status__in=[
                    Appointment.STATUS_PENDING,
                    Appointment.STATUS_CONFIRMED,
                    Appointment.STATUS_RESCHEDULE_PROPOSED,
                ],
            )
        ]

        slots: list[str] = []
        current = window_start.replace(second=0, microsecond=0)
        while current + step <= window_end:
            candidate_end = current + step
            if all(candidate_end <= busy_start or current >= busy_end for busy_start, busy_end in busy_ranges):
                slots.append(current.strftime("%H:%M"))
            current += step
        return slots

    def create_booking(
        self,
        *,
        service_ids: list[int],
        target_date: date,
        selected_time: str,
        resource_id: int | None,
        client: Any,
        notify_received: bool = True,
        **kwargs: Any,
    ) -> Any:
        feature_models = self.provider.get_feature_models()
        adapter = self._build_adapter(target_date=target_date)
        extra_fields = build_single_service_extra_fields(
            service_ids,
            kwargs.pop("extra_fields", None),
        )
        persistence_hook = LilyBookingPersistenceHook(
            feature_models.appointment_model,
            notify_received=notify_received,
        )
        return runtime_create_booking(
            adapter=adapter,
            cache_adapter=BookingCacheAdapter(),
            appointment_model=feature_models.appointment_model,
            service_ids=service_ids,
            target_date=target_date,
            selected_time=selected_time,
            resource_id=resource_id,
            client=client,
            extra_fields=extra_fields,
            persistence_hook=persistence_hook,
            **kwargs,
        )


_gateway = BookingRuntimeEngineGateway()


def get_booking_engine_gateway() -> BookingRuntimeEngineGateway:
    """Return the active engine gateway."""
    return _gateway
