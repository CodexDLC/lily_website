from pydantic import BaseModel


class ContactSummaryDto(BaseModel):
    category_id: str
    category_name: str
    total_count: int
    unread_count: int


class ContactPreviewDto(BaseModel):
    id: int
    first_name: str
    topic: str  # id темы
    message_preview: str
    is_processed: bool
    created_at: str  # ISO формат


class ContactDetailDto(ContactPreviewDto):
    phone: str | None = None
    message: str
