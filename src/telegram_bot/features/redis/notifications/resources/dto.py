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

    @field_validator("request_call", mode="before")
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
