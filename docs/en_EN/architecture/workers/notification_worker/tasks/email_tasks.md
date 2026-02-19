# 📜 Email Tasks

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

ARQ task for sending emails.

**File:** `src/workers/notification_worker/tasks/email_tasks.py`

## `send_email_task`

```python
async def send_email_task(ctx, recipient_email, subject, template_name, data):
```

1. Retrieves `NotificationService` from the ARQ context.
2. Calls `notification_service.send_notification(email, subject, template_name, data)`.
3. On success/failure, sends a status update via `send_status_update(ctx, appointment_id, "email", status)`.
