# 📜 Notification Tasks

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

ARQ tasks for booking notifications via Redis Streams.

**File:** `src/workers/notification_worker/tasks/notification_tasks.py`

## `send_booking_notification_task`

```python
async def send_booking_notification_task(ctx, appointment_data, admin_id=None):
```

Sends a `new_appointment` event to the `bot_events` Redis Stream. The bot's Redis listener picks it up and renders the admin notification in Telegram.

## `requeue_event_task`

```python
async def requeue_event_task(ctx, event_data):
```

Retry mechanism: re-adds an event to the `bot_events` stream with an incremented `_retries` counter.
