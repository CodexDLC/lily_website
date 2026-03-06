# 🛠️ Codex Tools (Technical Documentation)

[⬅️ Back to Main](../README.md)

This directory contains the standalone, framework-agnostic business logic toolkit `codex_tools`. It has been built using the **Hexagonal Architecture (Ports and Adapters)** pattern to easily migrate across Python applications (e.g., from Django to FastAPI).

## 🗂️ Module Map

### 1. Booking (`codex_tools.booking`)

The core booking engine. It computes available slots, checks service limits, and manages multi-service chains.

**Key Concepts:**
- **DTOs (`dto.py`)**: Immutable (`frozen=True`) Pydantic models. Everything passed to or returned from the engine is an explicit struct (e.g., `BookingEngineRequest`, `MasterAvailability`, `BookingChainSolution`).
- **Interfaces (`interfaces.py`)**: `typing.Protocol` definitions for dependency injection (e.g., `ScheduleProvider`, `BusySlotsProvider`).
- **Engine Core**: `SlotCalculator` handles sliding windows algorithms, and `ChainFinder` orchestrates finding available time across dependencies.
- **Adapters (`adapters/`)**: This is the only place where the library interacts with frameworks like Django. E.g., `DjangoAvailabilityAdapter` implements the interfaces by fetching Django ORM objects.

### 2. Notifications (`codex_tools.notifications`)

Abstract factory and builders for sending push/SMS/email notifications.
- Interacts with variables for message templating (`builder.py`).
- Framework-coupled adapters (e.g. `adapters/django_adapter.py`) exist to map abstract interfaces to concrete Django model structures.

### 3. Calendar (`codex_tools.codex_calendar`)

Simple calculation tools for date layouts, matrix rendering of days, weeks, and month boundaries (`engine.py`).

### 4. Common Utils (`codex_tools.common`)

A collection of corporate-level standalone utilities:
- **`logger.py`**: A universal setup block for `loguru` integrating perfectly with `logging` (suppressing noisy Django db logging).
- **`arq_client.py`**: Helper structure for pushing tasks into ARQ pipelines.
- **`cache.py`**: Abstract locking and caching mechanisms mapping to Django or raw Redis.
- **`phone.py`**: Formatting and validating phones based on international standards.

## 🤝 Adding Framework Support

To support a new framework (e.g., SQLAlchemy/FastAPI), simply create a new adapter in `adapters/[framework]_adapter.py` that conforms to the models defined in `dto.py`. The core engine logic requires absolutely zero changes.
