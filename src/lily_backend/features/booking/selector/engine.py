"""Scaffold-owned engine gateway for resource-slot booking."""

from __future__ import annotations

import logging
from datetime import date, timedelta
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

from ..providers.runtime import get_booking_project_data_provider

logger = logging.getLogger(__name__)

MULTI_SERVICE_MAX_UNIQUE_STARTS = 100
MULTI_SERVICE_MAX_SOLUTIONS = 1000


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

        counts: dict[int, int] = dict(
            self.appointment_model.objects.filter(
                master_id__in=[int(i) for i in resource_ids],
                datetime_start__date=target_date,
                status__in=["pending", "confirmed"],
            )
            .values("master_id")
            .annotate(cnt=Count("id"))
            .values_list("master_id", "cnt")
        )
        return sorted(resource_ids, key=lambda i: counts.get(int(i), 0))


class LilyBookingPersistenceHook:
    """Project persistence policy for chain bookings."""

    def __init__(self, appointment_model: type[Any]) -> None:
        self.appointment_model = appointment_model

    def persist_chain(
        self,
        solution: Any,
        service_ids: list[int],
        client: Any,
        extra_fields: dict[str, Any] | None = None,
    ) -> list[Any]:
        appointments: list[Any] = []
        for index, item in enumerate(getattr(solution, "items", [])):
            fields = (extra_fields or {}).copy()
            fields.update(
                {
                    "master_id": int(item.resource_id),
                    "service_id": service_ids[index] if index < len(service_ids) else service_ids[-1],
                    "datetime_start": item.start_time,
                    "duration_minutes": item.duration_minutes,
                    "client": client,
                }
            )
            appointments.append(self.appointment_model.objects.create(**fields))

        # Notify about received bookings
        from features.conversations.services.notifications import _get_engine

        engine = _get_engine()
        for appt in appointments:
            engine.dispatch_event("booking.received", appt)

        return appointments


class BookingRuntimeEngineGateway(BookingEngineGateway):
    """Feature-facing engine gateway."""

    def __init__(self, provider: Any = None) -> None:
        self.provider = provider or get_booking_project_data_provider()

    def _build_adapter(self, target_date: date | None = None) -> DjangoAvailabilityAdapter:
        from ..booking_settings import BookingSettings

        feature_models = self.provider.get_feature_models()
        strategy = BookingSettings.load().load_strategy
        return LoadAwareDjangoAvailabilityAdapter(
            resource_model=feature_models.resource_model,
            appointment_model=feature_models.appointment_model,
            service_model=feature_models.service_model,
            working_day_model=feature_models.working_day_model,
            day_off_model=feature_models.day_off_model,
            booking_settings_model=feature_models.booking_settings_model,
            site_settings_model=feature_models.site_settings_model,
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

        settings = BookingSettings.load()
        if settings.book_only_from_next_day and target_date <= dt_date.today():
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

        settings = BookingSettings.load()
        effective_search_from = search_from
        if settings.book_only_from_next_day and search_from <= dt_date.today():
            effective_search_from = dt_date.today() + timedelta(days=1)

        effective_kwargs = {key: value for key, value in kwargs.items() if value is not None}
        adapter = self._build_adapter(target_date=effective_search_from)
        return runtime_get_nearest_slots(adapter, service_ids, effective_search_from, **effective_kwargs)

    def get_resource_day_slots(
        self,
        *,
        resource_id: int,
        target_date: date,
    ) -> list[str]:
        from ..booking_settings import BookingSettings

        settings = BookingSettings.load()
        step = timedelta(minutes=settings.step_minutes or 30)
        adapter = self._build_adapter(target_date=target_date)
        availability = adapter.build_resources_availability(resource_ids=[resource_id], target_date=target_date)
        day_availability = availability.get(str(resource_id))
        if not day_availability or not day_availability.free_windows:
            return []

        slots: list[str] = []
        for window_start, window_end in day_availability.free_windows:
            current = window_start.replace(second=0, microsecond=0)
            while current + step <= window_end:
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
        **kwargs: Any,
    ) -> Any:
        feature_models = self.provider.get_feature_models()
        adapter = self._build_adapter(target_date=target_date)
        persistence_hook = LilyBookingPersistenceHook(feature_models.appointment_model)
        return runtime_create_booking(
            adapter=adapter,
            cache_adapter=BookingCacheAdapter(),
            appointment_model=feature_models.appointment_model,
            service_ids=service_ids,
            target_date=target_date,
            selected_time=selected_time,
            resource_id=resource_id,
            client=client,
            persistence_hook=persistence_hook,
            **kwargs,
        )


_gateway = BookingRuntimeEngineGateway()


def get_booking_engine_gateway() -> BookingRuntimeEngineGateway:
    """Return the active engine gateway."""
    return _gateway
