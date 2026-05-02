"""Project-owned booking persistence for Lily appointments."""

from __future__ import annotations

from typing import Any

from features.main.models import Service


class BookingServiceNotFoundError(ValueError):
    """Raised when the booking engine asks to persist an unknown service."""


class DuplicateChainAppointmentError(ValueError):
    """Raised when a booking engine solution would duplicate a chain item."""


def _load_services(service_ids: list[int]) -> dict[int, Service]:
    services = Service.objects.in_bulk(service_ids)
    missing_ids = [service_id for service_id in service_ids if service_id not in services]
    if missing_ids:
        raise BookingServiceNotFoundError(f"Booking service not found: {missing_ids[0]}")
    return services


def build_single_service_extra_fields(
    service_ids: list[int],
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return extra fields that make generic single-service persistence safe."""
    if len(service_ids) != 1:
        return dict(extra_fields or {})

    service = _load_services(service_ids)[service_ids[0]]
    fields = dict(extra_fields or {})
    fields["price"] = service.price
    return fields


def create_appointment_from_solution_item(
    *,
    appointment_model: type[Any],
    item: Any,
    service_id: int,
    service: Service,
    client: Any,
    extra_fields: dict[str, Any] | None = None,
) -> Any:
    """Create a Lily Appointment from one booking engine solution item."""
    fields = dict(extra_fields or {})
    fields.update(
        {
            "master_id": int(item.resource_id),
            "service_id": service_id,
            "datetime_start": item.start_time,
            "duration_minutes": item.duration_minutes,
            "client": client,
            "price": service.price,
        }
    )
    return appointment_model.objects.create(**fields)


def _active_statuses(appointment_model: type[Any]) -> list[str]:
    return [
        getattr(appointment_model, "STATUS_PENDING", "pending"),
        getattr(appointment_model, "STATUS_CONFIRMED", "confirmed"),
        getattr(appointment_model, "STATUS_RESCHEDULE_PROPOSED", "reschedule_proposed"),
    ]


def _validate_no_duplicate_chain_items(
    *,
    appointment_model: type[Any],
    items: list[Any],
    service_ids: list[int],
    client: Any,
) -> None:
    seen: set[tuple[int, Any]] = set()
    duplicate_keys: set[tuple[int, Any]] = set()

    for item, service_id in zip(items, service_ids, strict=False):
        key = (service_id, getattr(item, "start_time", None))
        if key in seen:
            duplicate_keys.add(key)
        seen.add(key)

    if duplicate_keys:
        raise DuplicateChainAppointmentError("Booking chain contains duplicate service/time items")

    if client is None:
        return

    existing_filters = [
        {
            "client": client,
            "service_id": service_id,
            "datetime_start": getattr(item, "start_time", None),
            "status__in": _active_statuses(appointment_model),
        }
        for item, service_id in zip(items, service_ids, strict=False)
    ]
    for filters in existing_filters:
        if filters["datetime_start"] is not None and appointment_model.objects.filter(**filters).exists():
            raise DuplicateChainAppointmentError("Client already has this service booked at the selected time")


class LilyBookingPersistenceHook:
    """Project persistence policy for chain and any-resource bookings."""

    def __init__(self, appointment_model: type[Any], *, notify_received: bool = True) -> None:
        self.appointment_model = appointment_model
        self.notify_received = notify_received

    def persist_chain(
        self,
        solution: Any,
        service_ids: list[int],
        client: Any,
        extra_fields: dict[str, Any] | None = None,
    ) -> list[Any]:
        items = list(getattr(solution, "items", []))
        if not items:
            return []
        if len(items) != len(service_ids):
            raise ValueError("Booking solution item count does not match requested services")

        _validate_no_duplicate_chain_items(
            appointment_model=self.appointment_model,
            items=items,
            service_ids=service_ids,
            client=client,
        )

        services = _load_services(service_ids)
        appointments = [
            create_appointment_from_solution_item(
                appointment_model=self.appointment_model,
                item=item,
                service_id=service_id,
                service=services[service_id],
                client=client,
                extra_fields=extra_fields,
            )
            for item, service_id in zip(items, service_ids, strict=False)
        ]

        if self.notify_received:
            self._dispatch_received(appointments)

        return appointments

    def _dispatch_received(self, appointments: list[Any]) -> None:
        from features.conversations.services.notifications import _get_engine

        engine = _get_engine()
        for appt in appointments:
            engine.dispatch_event("booking.received", appt)
