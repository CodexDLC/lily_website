# 📄 Notifications Service

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

The `NotificationsService` acts as the business logic layer for the notifications feature, coordinating between the Telegram bot, the Django backend, and the background workers.

## 🛠️ Core Responsibilities

Located in: `src/telegram_bot/features/telegram/notifications/logic/service.py`

### 1. `confirm_appointment(appointment_id: int) -> dict`

*   **API Call**: Sends a confirmation request to the Django backend via the `data_provider`.
*   **Worker Integration**: If the API call is successful, it calls `process_notification` to trigger the actual notification delivery (Email/SMS).

### 2. `cancel_appointment(appointment_id: int, reason_code: str, reason_text: str) -> dict`

*   **API Call**: Sends a cancellation request to Django with a specific reason code and note.
*   **Worker Integration**: Triggers a cancellation notification via `process_notification`.

### 3. `process_notification(appointment_id: int, status: str, reason_text: str | None = None)`

*   **ARQ Integration**: Enqueues a job named `send_appointment_notification` in the ARQ worker pool.
*   **Minimal Data Transfer**: Only the `appointment_id`, `status`, and `reason_text` are passed to the worker.
*   **Efficiency**: The worker is responsible for fetching the full booking details from the `AppointmentCache` (Redis), reducing the payload size and ensuring data consistency.

## 🧩 Key Design Decisions

*   **Decoupling**: The bot doesn't send emails or SMS directly. It only requests the backend to update the status and asks the worker to handle the delivery.
*   **Cache-First Worker**: By passing only the ID, we ensure the worker always uses the most up-to-date data stored in Redis, avoiding race conditions where the bot might have stale data.
*   **Error Handling**: Logs errors if the ARQ pool is not initialized or if enqueuing fails, ensuring system reliability.
