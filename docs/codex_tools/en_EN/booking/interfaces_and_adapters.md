# 🔌 Interfaces & Adapters

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

To decouple the booking logic from frameworks, `codex_tools` defines dependency rules known as "Ports and Adapters".

## Interfaces (`interfaces.py`)

The Engine expects basic protocols to ask the outside world for data.
- **`ScheduleProvider`**: Returns working hours and break intervals.
- **`BusySlotsProvider`**: Queries the database to list all existing appointments.

## Adapters (`adapters/`)

Adapters are implementations of these interfaces. They are the only files allowed to have `import django` or `import sqlalchemy`.

### `DjangoAvailabilityAdapter`

A reference adapter included natively for standard Django integrations.
- It inherits the interfaces and executes Django QuerySets.
- Processes models (like `Appointment`, `Master`, `Service`, `Schedule`).
- Emits pre-calculated Pydantic `MasterAvailability` instances to the Engine.

When adding `codex_tools` to a new framework, developers should replicate this adapter (e.g., `FastAPIAdapter`) and inject it into their views/routers.
