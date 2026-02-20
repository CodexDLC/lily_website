# 📄 Notifications Orchestrator (Redis)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

The `NotificationsOrchestrator` is the central logic hub for handling events coming from the Redis Stream. It manages the lifecycle of a notification from the moment it is received from the backend until it is updated with delivery statuses from workers.

## 🛠️ Core Responsibilities

Located in: `src/telegram_bot/features/redis/notifications/logic/orchestrator.py`

### 1. `handle_notification(raw_payload: dict[str, Any]) -> UnifiedViewDTO`

Processes new booking events from the backend.

*   **Validation**: Converts raw dictionary data into a `BookingNotificationPayload` DTO.
*   **Topic Routing**: Uses `_get_target_topic` to determine which Telegram Topic (forum thread) the message should be sent to, based on the service category.
*   **Rendering**: Calls `NotificationsUI.render_notification` to generate the initial message.
*   **Output**: Returns a `UnifiedViewDTO` with `mode="topic"` or `mode="channel"`.

### 2. `handle_status_update(message_data: dict[str, Any]) -> UnifiedViewDTO | None`

Processes delivery reports (Email/SMS) from autonomous workers.

*   **State Persistence**:
    1.  Retrieves the current booking data from `AppointmentCache` (Redis).
    2.  Updates the specific channel status (`email_delivery_status` or `twilio_delivery_status`).
    3.  Saves the updated state back to the cache.
*   **UI Synchronization**:
    *   Re-renders the **entire** notification card using the updated cache data.
    *   This ensures that "checkmarks" (✅) for delivery statuses are updated in real-time without losing other information.
*   **Mode**: Returns a `UnifiedViewDTO` with `mode="edit"` to update the existing message in Telegram.

### 3. `_get_target_topic(payload: BookingNotificationPayload) -> int | None`

Helper method to map `category_slug` to a specific `message_thread_id` using the bot's settings.

## 🧩 Data Flow: Status Updates

1.  **Worker** sends a status update to the Redis Stream (e.g., `channel="email", status="sent"`).
2.  **RedisStreamProcessor** routes the message to this orchestrator.
3.  **Orchestrator** updates the `AppointmentCache`.
4.  **Orchestrator** triggers a message edit in Telegram with the updated UI (e.g., showing a checkmark next to "Email").

## 📝 Related Components

*   **[📄 BookingNotificationPayload](../resources/dto.md)**: The data structure for notifications.
*   **[📄 NotificationsUI](../ui/ui.md)**: Responsible for the visual representation of statuses.
