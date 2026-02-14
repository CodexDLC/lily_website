from typing import Any

from pydantic import BaseModel, Field


class SiteSettingsSchema(BaseModel):
    """
    Pydantic-схема для настроек сайта.
    Обеспечивает типизацию и валидацию данных из Redis.
    """

    company_name: str = Field(default="LILY Beauty Salon")
    site_base_url: str = Field(default="https://lily-salon.de/")
    logo_url: str = Field(default="/static/img/logo_lily.webp")

    # Контакты
    phone: str = Field(default="+49 176 59423704")
    email: str = Field(default="info@lily-salon.de")
    address_street: str = Field(default="Lohmannstraße 111")
    address_locality: str = Field(default="Köthen (Anhalt)")
    address_postal_code: Any = Field(default="06366")

    # Гео
    latitude: Any = Field(default="51.746495")
    longitude: Any = Field(default="11.9784666")

    # Соцсети
    instagram_url: str = Field(default="https://instagram.com/manikure_kothen")
    telegram_url: str | None = None
    whatsapp_url: str | None = None

    # Часы работы (строки для отображения)
    working_hours_weekdays: str = Field(default="09:00 - 18:00")
    working_hours_saturday: str = Field(default="10:00 - 14:00")
    working_hours_sunday: str = Field(default="Geschlossen")

    # Технические пути
    url_path_contact_form: str = Field(default="/contacts/")
    url_path_confirm: str = Field(default="/appointments/confirm/{token}/")
    url_path_cancel: str = Field(default="/appointments/cancel/{token}/")
    url_path_reschedule: str = Field(default="/booking/")

    # Прочее
    price_range: str = Field(default="$$")
