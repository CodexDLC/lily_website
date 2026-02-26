# Logging Standard (Lily Protocol v1.1)

This document defines the unified logging format for the Lily Website project. All logs must follow this standard to ensure they are easily parsable by monitoring tools and human-readable.

## 1. Core Principles
- **Import:** Always use `from core.logger import log`.
- **Format:** Use the pipe-separated format: `[Category]: [Action] | key1=value1 | key2=value2 | ...`
- **Language:** English only.
- **IDs:** Always include relevant IDs (e.g., `request_id`, `client_id`, `appointment_id`).

## 2. Log Levels

### DEBUG (Process & Inputs)
Used for tracing execution flow and inspecting incoming data.
- **Format:** `[Category]: [Action] | [Data]`
- **Example:** `log.debug("Service: BookingSession | Action: Update | step=2 | service_id=15")`

### INFO (Success & Milestones)
Used for significant successful events. Visible in production console.
- **Format:** `[Category]: [Action] | [Data]`
- **Example:** `log.info("Task: send_booking_notification_task | Action: Success | appointment_id=123")`

### WARNING (Anomalies)
Used for unexpected but non-critical situations (e.g., invalid input handled by default).
- **Format:** `[Category]: [Action] | [Reason] | [Data]`
- **Example:** `log.warning("Service: BookingSession | Action: InvalidStep | reason=out_of_range | step=99")`

### ERROR (Failures)
Used for exceptions and critical failures. These are serialized to JSON for monitoring.
- **Format:** `[Category]: [Action] | [Error] | [Data]`
- **Example:** `log.error(f"Task: send_email | Action: Failed | error={e} | recipient=user@example.com")`

## 3. Categories
- `Service`: Business logic (Services, Selectors).
- `Task`: Background jobs (ARQ, Celery).
- `Command`: Management commands.
- `View`: Django views (Request/Response).
- `API`: External API calls or internal API endpoints.
- `Redis`: Cache and state management.

## 4. Implementation Example
```python
from core.logger import log

def process_order(order_id: int):
    log.debug(f"Service: OrderService | Action: Start | order_id={order_id}")
    try:
        # ... logic ...
        log.info(f"Service: OrderService | Action: Success | order_id={order_id}")
    except Exception as e:
        log.error(f"Service: OrderService | Action: Failed | order_id={order_id} | error={e}")
```
