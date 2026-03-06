# 📦 Booking DTOs

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

Data Transfer Objects are the primary interface for communicating with the Booking Engine.
All DTOs are declared in `codex_tools.booking.dto`. They use Pydantic `v2` and are strictly immutable (`frozen=True`) to prevent side effects during backtracking algorithms.

## Input DTOs

### `ServiceRequest`
Represents a single service requested by a client.

- `service_id (str)`: Unique ID of the service.
- `duration_minutes (int)`: Core duration.
- `gap_after_minutes (int)`: Time blocked after the service (for room cleaning, setup).
- `allowed_master_ids (list[str])`: Masters capable of performing this.

### `BookingEngineRequest`
The complete payload provided to `ChainFinder.find()`.

- `service_requests (list[ServiceRequest])`: The sequence of desired services.
- `target_date (date)`: Desired day.
- `mode (BookingMode)`: Can be `SINGLE_DAY` or `MULTIPLE_DAYS`.

## Availability DTOs

### `MasterAvailability`
Provided by the Adapter before the engine runs. Used by the Engine to know what times are free.

- `master_id (str)`
- `free_windows (list[tuple[datetime, datetime]])`: E.g., `[(09:00, 13:00), (14:00, 18:00)]`.
- `buffer_between_minutes (int)`: Global master padding required between different clients.

## Output DTOs

### `BookingChainSolution`
An individual valid configuration of appointments found by the engine.

- `services (list[SingleServiceSolution])`: The specific slots allocated.
- `span_minutes()`: Total time taken by the chain from the start of the first service to the end of the last.

### `EngineResult`
The final return object from `ChainFinder`.

- `chains (list[BookingChainSolution])`: Contains all possible solutions.
- `errors (list[str])`: If empty, it means slots were found or none exist. If populated, something was wrong with the request (e.g., conflicting master requirements).
