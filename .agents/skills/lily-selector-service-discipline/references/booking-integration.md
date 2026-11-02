# Lily Booking Integration

Read for booking availability, persistence, model wiring or cabinet workflow changes. Paths are relative to `src/lily_backend/` unless prefixed with `tests/`.

| Concern | Current application seam |
| --- | --- |
| ORM data/model wiring | `features/booking/providers/runtime.py`, `RuntimeBookingProvider` |
| Availability/runtime calls | `features/booking/selector/engine.py`, `BookingRuntimeEngineGateway` |
| Appointment persistence | `features/booking/persistence.py`, `LilyBookingPersistenceHook` |
| Cabinet workflow | `features/booking/services/cabinet.py` |
| Cabinet presentation bridge | `cabinet/booking_bridge.py`, `cabinet/services/booking.py` |
| Public commit/cart | `features/booking/views/public/commit.py`, `features/booking/dto/public_cart.py` |

The provider maps appointment/master/schedule models from booking, services from `features.main`, and clients from `system`. Reuse these mappings rather than introducing alternate models for a new screen.

Current distinctions to preserve unless explicitly changing their behavior:

- Bookable masters are active and have working days; services need active, scheduled masters. Cabinet service selection additionally filters active, non-planned categories. Do not silently make public and cabinet filters identical.
- The provider's blocking appointment statuses are pending, confirmed and reschedule-proposed. The cabinet schedule workflow has a different set that also includes completed/no-show; availability and schedule display are different contracts.
- Persistence loads service records, carries service price into appointments and guards duplicate chain items. Avoid writing appointments directly from a new UI path and bypassing this hook.
- `selector/engine.py` wraps runtime creation as well as reads; its directory name does not imply a pure read-only API.
- Public commit currently includes client lookup/creation and transaction orchestration. Do not claim it is already a thin view or refactor it as a side effect of a template task.

Library APIs are provided by the installed `codex-django` version declared in `pyproject.toml`/the lockfile. Locate its official usage skill when available; do not invent an installed skill or modify managed dependency files. Scaffold ownership comments are evidence to inspect, not permission to edit a separate library checkout.

Relevant existing tests (repository root): `tests/lily_backend/unit/test_booking_runtime_provider.py`, `test_booking_engine_gateway.py`, `test_cabinet_booking_service_wrapper.py` in that same unit directory, and `tests/lily_backend/integration/booking/`. Select tests by changed behavior; this list is not a mandatory full suite.
