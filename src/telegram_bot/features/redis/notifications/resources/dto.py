from pydantic import BaseModel, field_validator


class BookingNotificationPayload(BaseModel):
    """
    Модель данных для уведомления о новой брони.
    """

    id: int
    client_name: str
    first_name: str | None = ""
    last_name: str | None = ""
    client_phone: str
    client_email: str
    service_name: str
    master_name: str
    datetime: str
    duration_minutes: int = 30  # <--- ДОБАВИЛИ
    price: float
    request_call: bool
    client_notes: str | None = ""
    visits_count: int = 0
    category_slug: str | None = None
    active_promo_id: int | None = None
    active_promo_title: str | None = None

    @field_validator("request_call", mode="before")
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)


class ContactNotificationPayload(BaseModel):
    """
    Модель данных для уведомления из контактной формы.
    Обновлена для поддержки богатых данных из Redis.
    """

    request_id: int
    first_name: str | None = ""
    last_name: str | None = ""
    contact_value: str | None = ""
    contact_type: str | None = ""
    topic: str | None = ""
    message: str | None = ""
    created_at: str | None = ""

    # Для обратной совместимости, если где-то еще используется 'text'
    text: str | None = ""

    @field_validator("request_id", mode="before")
    @classmethod
    def parse_request_id(cls, v):
        return int(v)
