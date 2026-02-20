# 📜 Task Utils

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

Shared utilities for notification tasks.

**File:** `src/workers/notification_worker/tasks/utils.py`

## `send_status_update`

```python
async def send_status_update(ctx, appointment_id, channel: str, status: str):
```

Sends a delivery status event back to the `bot_events` Redis Stream. Used by Email and Twilio tasks to update the admin notification UI in Telegram.

**Payload:**

```python
{
    "type": "notification_status",
    "appointment_id": appointment_id,
    "channel": "email" | "twilio",
    "status": "success" | "failed",
}
```

The bot's Redis listener receives this and updates the notification message with ✅ or ❌ indicators.
