from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from codex_django.booking.selectors import (
    build_picker_day_rows,
    normalize_slot_payload,
)
from codex_django.booking.selectors import (
    parse_resource_selections as runtime_parse_resource_selections,
)
from core.logger import logger

from ..selector.engine import get_booking_engine_gateway


class CabinetBookingAvailabilityService:
    """Feature-level helper for cabinet booking date and slot availability."""

    def __init__(self, gateway: Any = None) -> None:
        self.gateway = gateway or get_booking_engine_gateway()

    def build_picker_days(
        self,
        *,
        start_date: date,
        horizon: int,
        service_ids: list[int] | None = None,
        locked_resource_id: int | None = None,
        resource_selections: dict[str, str] | None = None,
    ) -> list[dict[str, str | int | bool]]:
        service_ids = [int(service_id) for service_id in service_ids or [] if int(service_id) > 0]
        logger.debug(
            "Booking picker days requested: start_date={} horizon={} service_ids={} locked_resource_id={} resource_selections={}",
            start_date,
            horizon,
            service_ids,
            locked_resource_id,
            resource_selections,
        )
        available_dates = self.get_available_dates(
            start_date=start_date,
            horizon=horizon,
            service_ids=service_ids,
            locked_resource_id=locked_resource_id,
            resource_selections=resource_selections,
        )
        rows = build_picker_day_rows(
            start_date=start_date,
            horizon=max(horizon, 0),
            available_dates=available_dates,
            has_service_scope=bool(service_ids),
        )
        logger.debug("Booking picker days built: rows={} available_dates={}", len(rows), len(available_dates))
        return rows

    def get_available_dates(
        self,
        *,
        start_date: date,
        horizon: int,
        service_ids: list[int],
        locked_resource_id: int | None = None,
        resource_selections: dict[str, str] | None = None,
    ) -> set[str]:
        del locked_resource_id, resource_selections
        if not service_ids:
            logger.debug("Booking available dates skipped because no service_ids were provided.")
            return set()

        # Optimization: instead of full scheduling for each day (slow),
        # just check which weekdays have active masters for these services (fast).
        from ..models import MasterWorkingDay

        active_weekdays = set(
            MasterWorkingDay.objects.filter(
                master__status="active",
                master__services__id__in=service_ids,
            )
            .values_list("weekday", flat=True)
            .distinct()
        )

        available_dates: set[str] = set()
        for offset in range(max(horizon, 0)):
            target_date = start_date + timedelta(days=offset)
            if target_date.weekday() in active_weekdays:
                available_dates.add(target_date.isoformat())

        logger.debug(
            "Booking available dates resolved: start_date={} horizon={} service_ids={} available_dates={}",
            start_date,
            horizon,
            service_ids,
            sorted(available_dates),
        )
        return available_dates

    def get_slots(
        self,
        *,
        booking_date: str,
        service_ids: list[int],
        locked_resource_id: int | None = None,
        resource_selections: dict[str, str] | None = None,
    ) -> list[str]:
        if not booking_date or not service_ids:
            logger.debug(
                "Booking slots skipped because required params are missing: booking_date={} service_ids={}",
                booking_date,
                service_ids,
            )
            return []

        try:
            target_date = date.fromisoformat(booking_date)
        except ValueError:
            logger.warning("Booking slots received invalid date: {}", booking_date)
            return []

        try:
            result = self.gateway.get_available_slots(
                service_ids=service_ids,
                target_date=target_date,
                locked_resource_id=locked_resource_id,
                resource_selections=resource_selections,
            )
        except Exception as e:
            logger.error(
                "Booking slots lookup failed for date {}: {} (service_ids={})",
                booking_date,
                str(e),
                service_ids,
            )
            return []

        slots = normalize_slot_payload(result)
        if slots:
            logger.debug(
                "Booking slots resolved: booking_date={} service_ids={} slots={}",
                booking_date,
                service_ids,
                slots,
            )
            return slots
        logger.warning(
            "Booking slots returned empty/unsupported payload: booking_date={} service_ids={} payload_type={}",
            booking_date,
            service_ids,
            type(result).__name__,
        )
        return []


def parse_resource_selections(raw_value: str | None) -> dict[str, str] | None:
    """Project-level re-export of the library payload parser."""
    return runtime_parse_resource_selections(raw_value)
