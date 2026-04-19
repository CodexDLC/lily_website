from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ResponseHeader(BaseModel):
    success: bool = True
    message: str | None = None
    current_state: str | None = None
    next_state: str | None = None
    trace_id: str | None = None


class CoreResponseDTO(BaseModel, Generic[T]):  # noqa: UP046
    header: ResponseHeader
    payload: T | None = None


class UserUpsertDTO(BaseModel):
    telegram_id: int
    first_name: str
    username: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_premium: bool = False

    model_config = ConfigDict(from_attributes=True)


class SiteSettingsSchema(BaseModel):
    company_name: str = Field(default="LILY Beauty Salon")
    site_base_url: str = Field(default="https://lily-salon.de/")
    logo_url: str = Field(default="/static/img/_source/logo_lily.png")
    phone: str = Field(default="+49 176 59423704")
    email: str = Field(default="info@lily-salon.de")
    address_street: str = Field(default="Lohmannstraße 111")
    address_locality: str = Field(default="Köthen (Anhalt)")
    address_postal_code: Any = Field(default="06366")
    latitude: Any = Field(default="51.746495")
    longitude: Any = Field(default="11.9784666")
    instagram_url: str = Field(default="https://instagram.com/manikure_kothen")
    telegram_url: str | None = None
    whatsapp_url: str | None = None
    working_hours_weekdays: str = Field(default="09:00 - 18:00")
    working_hours_saturday: str = Field(default="10:00 - 14:00")
    working_hours_sunday: str = Field(default="Geschlossen")
    url_path_contact_form: str = Field(default="/contacts/")
    url_path_confirm: str = Field(default="/cabinet/appointments/confirm/{token}/")
    url_path_cancel: str = Field(default="/cabinet/appointments/cancel/{token}/")
    url_path_reschedule: str = Field(default="/cabinet/appointments/reschedule/{token}/")
    price_range: str = Field(default="$$")
