"""
API endpoints для управления записями из Telegram Bot.
"""

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from features.booking.models.appointment import Appointment
from features.booking.schemas.appointment_schemas import ManageAppointmentRequest, ManageAppointmentResponse
from loguru import logger as log
from ninja import Router
from ninja.security import APIKeyHeader


class BotApiKey(APIKeyHeader):
    """
    X-API-Key аутентификация для Telegram Bot.

    Проверяет наличие общего ключа между Bot и Django (BOT_API_KEY).
    """

    param_name = "X-API-Key"

    def authenticate(self, request, key):
        expected_key = getattr(settings, "BOT_API_KEY", None)
        if expected_key and key == expected_key:
            return key
        return None


router = Router(auth=BotApiKey())


@router.post("/appointments/manage/", response=ManageAppointmentResponse)
def manage_appointment(request, payload: ManageAppointmentRequest):
    """
    Universal endpoint для управления записью из Telegram Bot.

    Защищен X-API-Key аутентификацией.

    Поддерживает действия:
    - confirm: подтверждение заявки
    - cancel: отклонение заявки
    """
    appointment = get_object_or_404(Appointment, id=payload.appointment_id)

    from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

    if payload.action == "confirm":
        # Подтверждение заявки
        appointment.status = Appointment.STATUS_CONFIRMED
        appointment.save(update_fields=["status", "updated_at"])

        # Sync cache for the notification worker
        NotificationCacheManager.seed_appointment(appointment.id)

        log.info(f"Appointment #{appointment.id} confirmed by Bot admin")

        return ManageAppointmentResponse(success=True, message="Заявка подтверждена", appointment_id=appointment.id)

    elif payload.action == "cancel":
        # Отклонение заявки
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancel_reason = payload.cancel_reason or Appointment.CANCEL_REASON_OTHER
        appointment.cancel_note = payload.cancel_note or ""
        appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])

        # Sync cache for the notification worker
        NotificationCacheManager.seed_appointment(appointment.id)

        log.info(f"Appointment #{appointment.id} cancelled by admin: {payload.cancel_reason}")

        return ManageAppointmentResponse(success=True, message="Заявка отклонена", appointment_id=appointment.id)

    return ManageAppointmentResponse(
        success=False, message=f"Неизвестное действие: {payload.action}", appointment_id=appointment.id
    )
