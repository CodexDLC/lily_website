# 📂 Notification Worker Tasks

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

Asynchronous ARQ tasks for the Notification Worker.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📜 Task Aggregator](./task_aggregator.md)** | Combines all tasks into a single `FUNCTIONS` list |
| **[📜 Email Tasks](./email_tasks.md)** | Email sending via `NotificationService` |
| **[📜 Notification Tasks](./notification_tasks.md)** | Booking notifications via Redis Streams |
| **[📜 Twilio Tasks](./twilio_tasks.md)** | SMS/WhatsApp dispatch with fallback logic |
| **[📜 Utils](./utils.md)** | Status update helper for delivery tracking |
