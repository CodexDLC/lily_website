# 📜 Twilio Service

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

Service for sending notifications via Twilio (SMS, WhatsApp).

**File:** `src/workers/core/base_module/twilio_service.py`

## `TwilioService` Class

### Initialization

```python
def __init__(self, account_sid: str, auth_token: str, from_number: str):
```

Creates a Twilio `Client` instance with the provided credentials.

### Methods

#### `send_sms(to_number, message) -> bool`

Sends a plain SMS message. Formats the phone number to E.164 format automatically.

#### `send_whatsapp_template(to_number, content_sid, variables) -> bool`

Sends a WhatsApp message using an official Content Template (pre-approved by Meta). Uses `content_sid` and `content_variables` for structured messaging.

#### `send_whatsapp(to_number, message, media_url=None) -> bool`

Sends a free-form WhatsApp message. Optionally attaches a media URL (validated for absolute, non-local URLs).

### Helper Methods

- **`_format_phone(phone)`**: Normalizes phone numbers to E.164 format. Handles `+` prefix, German `0` prefix → `+49`.
- **`_is_valid_media_url(url)`**: Validates that a media URL is absolute and not localhost/backend.

### Error Handling

All send methods catch `TwilioRestException` and generic exceptions, log errors, and return `False` on failure.
