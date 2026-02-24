"""
Pydantic schemas для управления записями через Telegram Bot.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ManageAppointmentRequest(BaseModel):
    """
    Универсальная схема для управления записью из Telegram Bot.

    Поддерживает действия:
    - confirm: подтверждение заявки
    - cancel: отклонение заявки
    """

    appointment_id: int = Field(..., description="ID записи")
    action: Literal["confirm", "cancel"] = Field(..., description="Действие: confirm или cancel")
    cancel_reason: str | None = Field(None, description="Причина отмены (для action=cancel)")
    cancel_note: str | None = Field(None, description="Текстовая заметка (для action=cancel)")


class ManageAppointmentResponse(BaseModel):
    """Ответ от endpoint управления записью"""

    success: bool
    message: str
    appointment_id: int


class SlotItem(BaseModel):
    """Один доступный слот."""

    label: str
    datetime_str: str


class SlotsResponse(BaseModel):
    """Список доступных слотов для записи."""

    slots: list[SlotItem]
    booking_url: str


class ProposeRescheduleRequest(BaseModel):
    """Запрос на предложение альтернативного времени клиенту."""

    appointment_id: int = Field(..., description="ID записи")
    proposed_slots: list[str] = Field(..., description="Предложенные слоты (список строк label)")


class ProposeRescheduleResponse(BaseModel):
    """Ответ от endpoint предложения альтернативного времени."""

    success: bool
    message: str
    appointment_id: int


class CategorySummaryItem(BaseModel):
    """Сводка по одной категории услуг."""

    category_slug: str
    category_title: str
    total: int
    pending: int
    completed: int


class CategorySummaryResponse(BaseModel):
    """Список категорий со сводкой по записям."""

    categories: list[CategorySummaryItem]


class AppointmentListItem(BaseModel):
    """Краткая информация об одной записи для списка."""

    id: int
    client_name: str
    status: str
    datetime: str


class AppointmentListResponse(BaseModel):
    """Страница списка записей по категории."""

    items: list[AppointmentListItem]
    total: int
    page: int
    pages: int
