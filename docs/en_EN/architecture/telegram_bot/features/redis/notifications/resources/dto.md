# 📄 Booking Notification Payload (DTO)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

The `BookingNotificationPayload` is a Pydantic model used to validate and structure incoming booking data from the Redis Stream.

## 🛠️ Model: BookingNotificationPayload

Located in: `src/telegram_bot/features/redis/notifications/resources/dto.py`

### 📋 Fields

| Field | Type | Description |
|:---|:---|:---|
| `id` | `int` | Unique identifier for the booking (appointment ID) |
| `client_name` | `str` | Full name of the client |
| `first_name` | `str \| None` | Client's first name (optional) |
| `last_name` | `str \| None` | Client's last name (optional) |
| `client_phone` | `str` | Client's phone number (E.164 format) |
| `client_email` | `str` | Client's email address |
| `service_name` | `str` | Name of the booked service |
| `master_name` | `str` | Name of the master (provider) |
| `datetime` | `str` | Date and time of the appointment |
| `duration_minutes` | `int` | Duration of the service (default: 30) |
| `price` | `float` | Total price of the service |
| `request_call` | `bool` | Whether the client requested a callback |
| `client_notes` | `str \| None` | Additional notes from the client |
| `visits_count` | `int` | Number of previous visits by the client |
| `category_slug` | `str \| None` | Slug for the service category (used for topic routing) |
| `active_promo_id` | `int \| None` | ID of the active promotion applied |
| `active_promo_title` | `str \| None` | Title of the active promotion |

### 🔍 Validation Logic

*   **`request_call`**: Includes a custom validator (`parse_bool`) that handles string inputs like `"true"`, `"1"`, `"yes"`, or `"on"`, converting them to a boolean. This ensures compatibility with various data sources (e.g., web forms).

## 📝 Usage

This DTO is primarily used by the `NotificationsOrchestrator` to:
1.  Validate raw data from Redis.
2.  Pass structured data to the `NotificationsUI` for rendering.
3.  Store and retrieve booking information from the `AppointmentCache`.
