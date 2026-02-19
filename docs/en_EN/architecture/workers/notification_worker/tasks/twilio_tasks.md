# 📜 Twilio Tasks

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

ARQ tasks for SMS and WhatsApp notifications via Twilio.

**File:** `src/workers/notification_worker/tasks/twilio_tasks.py`

## `send_twilio_task`

```python
async def send_twilio_task(ctx, phone_number, message, appointment_id=None, media_url=None, variables=None):
```

Multi-channel dispatch with fallback:

1. **WhatsApp Template** (if `variables` and `TWILIO_WHATSAPP_TEMPLATE_SID` set)
2. **WhatsApp Free-form** (with optional media)
3. **SMS** (final fallback)

Each attempt logs success/failure and sends a status update.

## `send_appointment_notification`

```python
async def send_appointment_notification(ctx, appointment_id, status, reason_text=None):
```

Autonomous notification dispatcher. Orchestrates both Email and Twilio tasks:

1. Loads appointment data from Redis cache (`notifications:cache:{id}`).
2. **Email**: Enqueues `send_email_task` with confirmation or cancellation template.
3. **Twilio**: Prepares WhatsApp template variables (date, time, name) and enqueues `send_twilio_task`.
