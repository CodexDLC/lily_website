# 📄 Notifications Orchestrator (Telegram)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

The `NotificationsOrchestrator` handles all user interactions (callbacks) related to booking notifications in the Telegram admin channel.

## 🛠️ Core Responsibilities

Located in: `src/telegram_bot/features/telegram/notifications/logic/orchestrator.py`

### 1. `handle_action(callback_data: NotificationsCallback, call: CallbackQuery) -> UnifiedViewDTO`

The main dispatcher for incoming callbacks. It maps action codes to specific handler methods.

*   **Supported Actions**:
    *   `approve`: Confirms the booking.
    *   `reject`: Opens the rejection reasons menu.
    *   `reject_busy`, `reject_ill`, etc.: Cancels the booking with a specific reason.
    *   `cancel_reject`: Returns to the main notification view.
    *   `delete_notification`: Deletes the message and cleans up history.

### 2. `_handler_approve(context: QueryContext) -> UnifiedViewDTO`

*   Calls `NotificationsService.confirm_appointment`.
*   On success, updates the message text to "Approved" and appends initial "waiting" (⏳) statuses for Email and SMS.
*   Returns an alert to the admin confirming the action.

### 3. `_reject_with_reason(context: QueryContext, reason_code: str, reason_text: str) -> UnifiedViewDTO`

*   Calls `NotificationsService.cancel_appointment` with the provided reason.
*   Updates the message text to "Rejected" and displays the reason.
*   Returns an alert to the admin.

### 4. `handle_status_update(payload: dict[str, Any], current_text: str | None = None) -> UnifiedViewDTO | None`

*   This method is a secondary handler for status updates (similar to the Redis orchestrator).
*   It uses `AppointmentCache` to reconstruct the full message text and update the delivery status icons (✅/❌).
*   **Note**: This ensures that even if the message was edited by an admin action, the background delivery statuses still get updated correctly.

## 🧩 Integration

*   **`NotificationsService`**: Used for all business logic and API calls.
*   **`NotificationsUI`**: Used for rendering the updated message content and keyboards.
*   **`UnifiedViewDTO`**: The standard return type for all handlers, specifying how the bot should update the Telegram UI (edit, alert, delete).
