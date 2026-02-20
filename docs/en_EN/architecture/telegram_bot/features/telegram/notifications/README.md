# 📂 Telegram Notifications (Admin Actions)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

The `telegram/notifications` feature handles interactive admin actions in Telegram, such as approving or rejecting bookings. It works in tandem with the `redis/notifications` feature, which provides the initial message.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📂 Handlers](./handlers/README.md)** | Callback processing for admin actions |
| **[📂 Logic](./logic/README.md)** | Orchestrator and service layer |
| **[📂 Contracts](./contracts/README.md)** | Data access interfaces |
| **[📂 UI](./ui/README.md)** | Message rendering and status views |
| **[📂 Resources](./resources/README.md)** | Texts, callbacks, keyboards |
| **[📂 Tests](./tests/README.md)** | Unit and integration tests |

## 📋 feature_setting.py

```python
class NotificationsStates(StatesGroup):
    main = State()

STATES = NotificationsStates
GARBAGE_COLLECT = True

MENU_CONFIG = {
    "key": "notifications",
    "text": "✨ Notifications",
    "priority": 50,
    "is_admin": True,
}
```

## 🔄 Logic Flow (Approval)

1. **Admin Clicks "Approve"**: Telegram sends a callback to the bot.
2. **Orchestrator**: Calls `NotificationsService.confirm_appointment`.
3. **Service**: Sends request to Django API; enqueues `send_appointment_notification` in ARQ.
4. **UI**: Updates Telegram message to show "Approved" with delivery status indicators.

## 🔄 Logic Flow (Rejection)

1. **Admin Clicks "Reject"**: Bot shows a menu of reasons (Busy, Ill, No Materials, etc.).
2. **Admin Selects Reason**: Bot calls `cancel_appointment` with the specific reason code.
3. **Service**: Updates Django and enqueues a cancellation notification job.
4. **UI**: Updates message to show "Rejected" with the chosen reason.

## 📝 Related Components

- **[📂 Redis Notifications](../../redis/notifications/README.md)**: The feature that creates the initial notification.
