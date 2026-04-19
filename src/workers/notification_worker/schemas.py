from typing import Any

from pydantic import BaseModel, Field, model_validator


class RecipientSchema(BaseModel):
    """Recipient contact information."""

    email: str | None = None
    phone: str | None = None
    first_name: str = "Guest"
    last_name: str = ""


class NotificationPayload(BaseModel):
    """
    Universal payload for any notification.
    Can trigger Email, Telegram, or both.
    """

    notification_id: str = Field(..., description="Unique ID for tracking")
    recipient: RecipientSchema = Field(default_factory=RecipientSchema)

    # New flat fields from codex-django 0.4+
    recipient_email: str | None = None
    recipient_phone: str | None = None
    client_name: str | None = None

    # Email specific
    template_name: str | None = Field(None, description="Short template name, e.g., 'bk_confirmation'")
    subject: str | None = None

    # Telegram/Bot specific
    event_type: str | None = Field(None, description="Event type for the bot, e.g., 'new_contact_request'")

    # Routing
    channels: list[str] = Field(default_factory=lambda: ["email"])
    context_data: dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "ignore"

    @model_validator(mode="before")
    @classmethod
    def bridge_flat_to_recipient(cls, data: Any) -> Any:
        """
        Adapts codex-django 0.4+ flat payloads to the worker's internal
        nested recipient structure.
        """
        if not isinstance(data, dict):
            return data

        recipient = data.get("recipient")
        r_email = data.get("recipient_email")
        r_phone = data.get("recipient_phone")
        c_name = data.get("client_name")

        # If we have flat fields but no recipient, build the recipient
        if not recipient and (r_email or r_phone or c_name):
            first_name = "Guest"
            last_name = ""
            if c_name:
                parts = c_name.split(maxsplit=1)
                first_name = parts[0]
                if len(parts) > 1:
                    last_name = parts[1]

            data["recipient"] = {
                "email": r_email,
                "phone": r_phone,
                "first_name": first_name,
                "last_name": last_name,
            }

        return data
