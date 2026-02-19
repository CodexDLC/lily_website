# 📄 Notifications UI (Redis)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

The `NotificationsUI` service is responsible for the visual representation of booking notifications and their delivery statuses in Telegram.

## 🛠️ Class: NotificationsUI

Located in: `src/telegram_bot/features/redis/notifications/ui/ui.py`

This class handles the rendering of HTML messages and the construction of inline keyboards for the admin channel.

### 🔍 Method: `render_notification`

Generates a complete notification card based on the current state of the booking.

#### Parameters

*   **`payload: BookingNotificationPayload`**: The structured data for the booking.
*   **`topic_id: int | None`**: The Telegram Topic ID (if applicable).
*   **`email_status: str`**: The current delivery status of the email notification (e.g., `"waiting"`, `"sent"`, `"failed"`, `"none"`).
*   **`twilio_status: str`**: The current delivery status of the SMS/WhatsApp notification (e.g., `"waiting"`, `"sent"`, `"failed"`, `"none"`).

#### Logic

1.  **Formatting**: Calls `format_new_booking` to generate the HTML text. This formatter includes visual indicators (like ✅ or ⏳) based on the `email_status` and `twilio_status`.
2.  **Keyboard Selection**:
    *   **Initial State**: If both statuses are `"none"`, it builds the main keyboard (`build_main_kb`) with "Approve" and "Reject" buttons.
    *   **Post-Action State**: If any status is not `"none"` (meaning an action has been taken), it builds a post-action keyboard (`build_post_action_kb`) which typically contains a "Delete" button to clean up the chat.

## 📝 Key Features

*   **Dynamic Status Indicators**: The UI automatically updates to show the progress of background workers (Email/SMS).
*   **Context-Aware Keyboards**: Buttons change based on the lifecycle of the notification (e.g., you cannot "Approve" a booking that is already being processed).
*   **HTML Support**: Uses Telegram's HTML parse mode for rich text formatting (bold, links, emojis).

## 🧩 Related Components

*   **[📄 NotificationsOrchestrator](../logic/orchestrator.md)**: Calls this UI service to generate views.
*   **[📄 Formatters](../resources/formatters.md)**: Contains the actual HTML templates.
