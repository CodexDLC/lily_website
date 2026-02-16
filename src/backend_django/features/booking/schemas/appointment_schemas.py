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
