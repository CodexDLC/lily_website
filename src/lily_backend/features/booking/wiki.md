# Resource-Slot Booking Module

## Quick Start

1. Add `"booking"` to `INSTALLED_APPS`
2. Run migrations: `python manage.py makemigrations booking && python manage.py migrate`
3. Add URLs to root `urls.py`:
   ```python
   path("booking/", include("booking.urls")),
   ```
4. Add cabinet URL to `cabinet/urls.py`:
   ```python
   from cabinet.views.booking import my_bookings_view
   path("my/bookings/", my_bookings_view, name="my_bookings"),
   ```

## Admin Setup

1. Create a `BookingSettings` model in `system/models/` extending `AbstractBookingSettings`
2. Register it in admin — configure `step_minutes`, `default_buffer_between_minutes`, etc.
3. Add masters via the Master admin (each master needs a linked User)
4. Set up working days for each master (Mon-Sun schedule)
5. Add services with durations and link them to masters

## How It Works

The booking wizard is a multi-step resource-slot flow:

1. **Select Service** — client picks a service
2. **Select Date** — calendar view, HTMX loads available dates
3. **Select Time** — available slots rendered as buttons
4. **Confirm** — summary and final submission

All slot computation is handled by the `codex_django.booking` resource-slot
engine via the adapter pattern. This app is an integration scaffold, not a
final project-specific booking product.

## Customizing Templates

Override any template by placing your version in your project's `templates/` dir:

- `booking/booking_page.html` — main wrapper
- `booking/partials/step_service.html` — service selection step
- `booking/partials/step_date.html` — calendar step
- `booking/partials/step_time.html` — time slots step
- `booking/partials/step_confirm.html` — confirmation step
- `cabinet/booking/my_bookings.html` — cabinet bookings list

## CSS Variables

The public booking templates use CSS custom properties for theming:

```css
:root {
    --booking-primary: #2563eb;
    --booking-primary-hover: #1d4ed8;
    --booking-bg: #ffffff;
    --booking-bg-secondary: #f8fafc;
    --booking-text: #1e293b;
    --booking-text-muted: #64748b;
    --booking-border: #e2e8f0;
    --booking-radius: 8px;
    --booking-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

Override these in your site CSS to match your brand.

## URL Configuration

Public booking page:
- `GET /booking/` — wizard page
- `GET /booking/calendar/?service_id=1&year=2026&month=3` — calendar partial (HTMX)
- `GET /booking/slots/?service_id=1&date=2026-03-25` — time slots partial (HTMX)
- `POST /booking/confirm/` — create booking

Cabinet:
- `GET /cabinet/my/bookings/` — client's bookings list

## Multi-service Bookings

By default the booking wizard runs in **solo mode** (one service per booking).
To support booking multiple services in a single session, implement `BookingPersistenceHook`.

### 1. Implement the hook

Create `booking/hooks.py` in your project:

```python
from __future__ import annotations
from typing import Any
from .models import Appointment


class MyBookingPersistenceHook:
    """Persists a multi-service chain as individual Appointment rows."""

    def persist_chain(
        self,
        solution: Any,
        service_ids: list[int],
        client: Any,
        extra_fields: dict[str, Any] | None = None,
    ) -> list[Appointment]:
        appointments = []
        for item in solution.items:
            appointments.append(
                Appointment.objects.create(
                    master_id=item.resource_id,
                    service_id=item.service_id,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    client=client,
                    **(extra_fields or {}),
                )
            )
        return appointments
```

### 2. Wire it into the confirm view

In `booking/views.py`, find the TODO comment and replace it:

```python
from .hooks import MyBookingPersistenceHook

# inside confirm_booking_view, replace the TODO block:
if len(service_ids) > 1:
    persistence_hook = MyBookingPersistenceHook()
```

### 3. Update the confirm form

Your form should send multiple `service_ids` values:

```html
<input type="hidden" name="service_ids" value="3">
<input type="hidden" name="service_ids" value="7">
<!-- optional per-service resource selection as JSON -->
<input type="hidden" name="resource_selections" value='{"3": 10, "7": null}'>
```

A `null` value for a service means "any available executor/resource".
