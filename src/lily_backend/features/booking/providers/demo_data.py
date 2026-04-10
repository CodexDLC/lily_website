"""Sandbox demo data for the resource-slot booking prototype.

This module is intentionally sandbox-only. It keeps the cabinet prototype
explorable without pretending that these dict payloads are part of the
runtime library or future CLI scaffold output.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

_MASTERS: list[dict[str, Any]] = [
    {"id": 1, "name": "Alexander Petrov", "specialty": "Barber", "avatar": "AP"},
    {"id": 2, "name": "Elena Sidorova", "specialty": "Stylist", "avatar": "ES"},
    {"id": 3, "name": "Dmitry Ivanov", "specialty": "Colorist", "avatar": "DI"},
    {"id": 4, "name": "Maria Sokolova", "specialty": "Manicure", "avatar": "MS"},
]

_CLIENTS: list[dict[str, Any]] = [
    {"id": 1, "name": "Anna Johnson", "phone": "+49 160 123 4567", "email": "anna@example.com", "visits": 12},
    {"id": 2, "name": "Maria Smith", "phone": "+49 151 555 1234", "email": "maria@example.com", "visits": 5},
    {"id": 3, "name": "Nina Miller", "phone": "+49 170 987 6543", "email": "nina@example.com", "visits": 3},
    {"id": 4, "name": "Alice Brown", "phone": "+49 151 222 3344", "email": "alice@example.com", "visits": 1},
]

_SERVICES: list[dict[str, Any]] = [
    {
        "id": 1,
        "title": "Classic Manicure",
        "price": 1200,
        "duration": 45,
        "category": "nails",
        "master_ids": [4],
        "exclusive_group": "nails_manicure_base",
        "conflicts_with": [2],
        "replacement_mode": "replace",
    },
    {
        "id": 2,
        "title": "Gel Polish",
        "price": 1800,
        "duration": 60,
        "category": "nails",
        "master_ids": [4],
        "exclusive_group": "nails_manicure_base",
        "conflicts_with": [1],
        "replacement_mode": "replace",
    },
    {"id": 3, "title": "Haircut (Men)", "price": 1500, "duration": 30, "category": "hair", "master_ids": [1, 2]},
    {"id": 4, "title": "Hair Coloring", "price": 5000, "duration": 120, "category": "hair", "master_ids": [2, 3]},
    {"id": 5, "title": "Lash Extension", "price": 3500, "duration": 90, "category": "lashes", "master_ids": [2, 4]},
]

_APPOINTMENTS: list[dict[str, Any]] = [
    {
        "id": 101,
        "master_id": 1,
        "time": "09:00",
        "client_name": "John Doe",
        "phone": "+49 170 111 2233",
        "service_title": "Haircut",
        "status": "confirmed",
        "price": 1500,
        "duration": 60,
        "date": "2026-03-24",
    },
    {
        "id": 102,
        "master_id": 1,
        "time": "11:30",
        "client_name": "Jane Smith",
        "phone": "+49 170 987 6543",
        "service_title": "Beard Trim",
        "status": "pending",
        "price": 800,
        "duration": 30,
        "date": "2026-03-24",
    },
    {
        "id": 103,
        "master_id": 2,
        "time": "10:00",
        "client_name": "Alice Brown",
        "phone": "+49 151 222 3344",
        "service_title": "Hair Styling",
        "status": "confirmed",
        "price": 2500,
        "duration": 120,
        "date": "2026-03-24",
    },
    {
        "id": 201,
        "master_id": 1,
        "time": "12:30",
        "client_name": "Smith N.",
        "phone": "+49 170 987 6543",
        "service_title": "Brow Design + Tinting",
        "status": "pending",
        "price": 25,
        "duration": 45,
        "date": "2026-03-23",
    },
    {
        "id": 202,
        "master_id": 2,
        "time": "10:00",
        "client_name": "Miller M.",
        "phone": "+49 151 555 1234",
        "service_title": "Haircut + Styling",
        "status": "pending",
        "price": 55,
        "duration": 75,
        "date": "2026-03-23",
    },
    {
        "id": 203,
        "master_id": 3,
        "time": "13:00",
        "client_name": "Wilson K.",
        "phone": "+49 163 444 5566",
        "service_title": "Facial Treatment",
        "status": "pending",
        "price": 80,
        "duration": 90,
        "date": "2026-03-23",
    },
]


def get_masters() -> list[dict[str, Any]]:
    return [dict(item) for item in _MASTERS]


def get_clients() -> list[dict[str, Any]]:
    return [dict(item) for item in _CLIENTS]


def get_services() -> list[dict[str, Any]]:
    return [dict(item) for item in _SERVICES]


def get_appointments() -> list[dict[str, Any]]:
    return [dict(item) for item in _APPOINTMENTS]


def get_master_by_column(col: int) -> dict[str, Any] | None:
    masters = get_masters()
    if 0 <= col < len(masters):
        return masters[col]
    return None


def get_slot_time(row: int, *, day_start: int = 8) -> str:
    hour = day_start + (row // 2)
    minute = 30 if row % 2 else 0
    return f"{hour:02d}:{minute:02d}"


def get_services_for_master(master_id: int | None) -> list[dict[str, Any]]:
    services = get_services()
    if master_id is None:
        return services
    return [service for service in services if master_id in service.get("master_ids", [])]


def get_available_slot_options(master_id: int, booking_date: str) -> list[str]:
    taken = {
        appointment["time"]
        for appointment in _APPOINTMENTS
        if int(appointment["master_id"]) == int(master_id) and appointment["date"] == booking_date
    }
    options: list[str] = []
    current = datetime.strptime(f"{booking_date} 09:00", "%Y-%m-%d %H:%M")
    last = datetime.strptime(f"{booking_date} 18:00", "%Y-%m-%d %H:%M")
    while current <= last:
        label = current.strftime("%H:%M")
        if label not in taken:
            options.append(label)
        current += timedelta(minutes=30)
    return options


def create_client(*, name: str, phone: str, email: str = "") -> dict[str, Any]:
    next_id = max((int(client["id"]) for client in _CLIENTS), default=0) + 1
    client = {"id": next_id, "name": name, "phone": phone, "email": email, "visits": 0}
    _CLIENTS.append(client)
    return dict(client)


def create_appointment(
    *,
    master_id: int,
    booking_date: str,
    start_time: str,
    service_id: int,
    client_name: str,
    client_phone: str,
    client_email: str = "",
) -> dict[str, Any]:
    service = next((item for item in _SERVICES if int(item["id"]) == int(service_id)), None)
    master = next((item for item in _MASTERS if int(item["id"]) == int(master_id)), None)
    next_id = max((int(item["id"]) for item in _APPOINTMENTS), default=200) + 1
    appointment = {
        "id": next_id,
        "master_id": master_id,
        "time": start_time,
        "client_name": client_name,
        "phone": client_phone,
        "email": client_email,
        "service_title": service["title"] if service else "Service",
        "status": "confirmed",
        "price": service["price"] if service else 0,
        "duration": service["duration"] if service else 30,
        "date": booking_date,
        "master_name": master["name"] if master else "",
        "service_id": service_id,
    }
    _APPOINTMENTS.append(appointment)
    return dict(appointment)


def update_appointment(booking_id: int, **updates: Any) -> dict[str, Any] | None:
    for appointment in _APPOINTMENTS:
        if int(appointment["id"]) == int(booking_id):
            appointment.update(updates)
            return dict(appointment)
    return None


def add_appointment(record: dict[str, Any]) -> dict[str, Any]:
    _APPOINTMENTS.append(dict(record))
    return dict(record)


def cancel_appointment(booking_id: int) -> dict[str, Any] | None:
    for index, appointment in enumerate(_APPOINTMENTS):
        if int(appointment["id"]) == int(booking_id):
            removed = _APPOINTMENTS.pop(index)
            return dict(removed)
    return None
