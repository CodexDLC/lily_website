# 📂 Notifications Handlers

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

Callback handlers for the Telegram Notifications feature. Processes admin actions (approve, reject) on booking notification messages.

## 📋 Registered Handlers

| Trigger | Description |
|:---|:---|
| `NotificationCallback(action=approve)` | Confirm appointment and enqueue notifications |
| `NotificationCallback(action=reject)` | Show rejection reason menu |
| `NotificationCallback(action=reason_*)` | Process specific rejection reason |
