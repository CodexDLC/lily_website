# 📜 Task Aggregator

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

Aggregates all worker-specific tasks with core tasks into a single `FUNCTIONS` list.

**File:** `src/workers/notification_worker/tasks/task_aggregator.py`

## `FUNCTIONS`

```python
FUNCTIONS = [
    send_booking_notification_task,
    send_email_task,
    send_appointment_notification,
    send_twilio_task,
] + CORE_FUNCTIONS
```

This list is referenced by `WorkerSettings.functions` and registered with the ARQ worker at startup.
