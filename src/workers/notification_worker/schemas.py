from typing import Any

from pydantic import BaseModel, Field


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
    recipient: RecipientSchema

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
