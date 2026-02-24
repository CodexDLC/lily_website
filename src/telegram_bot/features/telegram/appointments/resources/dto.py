from pydantic import BaseModel


class CategorySummaryDto(BaseModel):
    """Сводка по одной категории услуг."""

    category_slug: str
    category_title: str
    total: int
    pending: int
    completed: int


class AppointmentItemDto(BaseModel):
    """Краткая информация об одной записи для списка."""

    id: int
    client_name: str
    status: str
    datetime: str
