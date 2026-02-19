# 📄 Notifications API Provider

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

The `NotificationsApiProvider` is the concrete implementation of the `NotificationsDataProvider` protocol. It handles communication with the Django backend for managing appointment confirmations and cancellations.

## 🛠️ Class: NotificationsApiProvider

Located in: `src/telegram_bot/infrastructure/api_route/notifications.py`

This provider uses the `BaseApiClient` to perform structured HTTP requests to the backend's management endpoints.

### 🔍 Core Methods

#### 1. `confirm_appointment(appointment_id: int) -> dict`

Sends a confirmation request for a specific appointment.

*   **Method**: `POST`
*   **Endpoint**: `/api/v1/booking/appointments/manage/`
*   **Payload**:
    ```json
    {
      "appointment_id": 123,
      "action": "confirm"
    }
    ```
*   **Returns**: A dictionary containing the API response (e.g., `{"success": true}`).

#### 2. `cancel_appointment(appointment_id: int, reason: str | None = None, note: str | None = None) -> dict`

Sends a cancellation request with an optional reason and note.

*   **Method**: `POST`
*   **Endpoint**: `/api/v1/booking/appointments/manage/`
*   **Payload**:
    ```json
    {
      "appointment_id": 123,
      "action": "cancel",
      "cancel_reason": "master_busy",
      "cancel_note": "Master is busy at this time"
    }
    ```
*   **Returns**: A dictionary containing the API response.

## 🧩 Integration

*   **`BaseApiClient`**: All requests are routed through the base client to handle authentication, base URLs, and error logging.
*   **`NotificationsService`**: This provider is injected into the service layer, allowing the bot to trigger backend actions without knowing the specific API details.

## 📝 Note on Evolution

While the initial structure was auto-generated as a standard CRUD provider, it has been specialized to match the specific requirements of the booking management flow.
