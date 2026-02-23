"""
API endpoints для управления записями из Telegram Bot.
"""

from datetime import timedelta

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from features.booking.models.appointment import Appointment
from features.booking.schemas.appointment_schemas import (
    ManageAppointmentRequest,
    ManageAppointmentResponse,
    ProposeRescheduleRequest,
    ProposeRescheduleResponse,
    SlotItem,
    SlotsResponse,
)
from features.booking.services.slots import SlotService
from features.system.models.site_settings import SiteSettings
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


@router.get("/slots/", response=SlotsResponse)
def get_available_slots(request, appointment_id: int):
    """
    Возвращает доступные слоты для записи начиная с даты отменяемой записи.

    Используется Telegram Bot при предложении альтернативного времени клиенту.
    Ищет до 5 слотов в диапазоне 7 дней начиная с даты оригинальной записи.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    slot_service = SlotService()

    site_settings = SiteSettings.load()
    booking_url = ""
    url_path = getattr(site_settings, "url_path_booking", None) or "/booking/"
    site_base_url = getattr(site_settings, "site_base_url", "") or ""
    booking_url = f"{site_base_url.rstrip('/')}{url_path}"

    collected: list[SlotItem] = []
    start_date = timezone.localtime(appointment.datetime_start).date()

    weekday_names = {0: "Mo", 1: "Di", 2: "Mi", 3: "Do", 4: "Fr", 5: "Sa", 6: "So"}

    for delta in range(7):
        if len(collected) >= 5:
            break
        check_date = start_date + timedelta(days=delta)
        slots = slot_service.get_available_slots(
            masters=appointment.master,
            date_obj=check_date,
            duration_minutes=appointment.duration_minutes,
        )
        for time_str in slots:
            if len(collected) >= 5:
                break
            day_name = weekday_names.get(check_date.weekday(), "")
            label = f"{day_name}, {check_date.strftime('%d.%m')} um {time_str}"
            datetime_str = f"{check_date.strftime('%d.%m.%Y')} {time_str}"
            collected.append(SlotItem(label=label, datetime_str=datetime_str))

    return SlotsResponse(slots=collected, booking_url=booking_url)


@router.post("/appointments/propose/", response=ProposeRescheduleResponse)
def propose_reschedule(request, payload: ProposeRescheduleRequest):
    """
    Отменяет запись (причина: reschedule) и отправляет клиенту email
    с предложением альтернативного времени и ссылкой на booking.

    Вызывается из Telegram Bot когда admin выбирает слот для предложения.
    """
    appointment = get_object_or_404(Appointment, id=payload.appointment_id)

    appointment.status = Appointment.STATUS_CANCELLED
    appointment.cancelled_at = timezone.now()
    appointment.cancel_reason = Appointment.CANCEL_REASON_RESCHEDULE
    appointment.cancel_note = "Предложено альтернативное время"
    appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])

    import json

    from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

    NotificationCacheManager.seed_appointment(appointment.id)

    redis_client = NotificationCacheManager.get_redis_client()
    raw = redis_client.get(f"{NotificationCacheManager.APPOINTMENT_CACHE_PREFIX}{appointment.id}")
    cache_data: dict = json.loads(raw) if raw else {}
    client_email = cache_data.get("client_email") or ""

    if client_email and client_email != "не указан":
        site_settings = SiteSettings.load()
        url_path = getattr(site_settings, "url_path_booking", None) or "/booking/"
        site_base_url = getattr(site_settings, "site_base_url", "") or ""
        booking_url = f"{site_base_url.rstrip('/')}{url_path}"

        email_data = {
            **cache_data,
            "proposed_slots": payload.proposed_slots,
            "link_reschedule": booking_url,
        }

        try:
            from core.arq.client import DjangoArqClient

            DjangoArqClient.enqueue_job(
                "send_email_task",
                recipient_email=client_email,
                subject="Terminvorschlag - Lily Beauty Salon",
                template_name="reschedule_offer.html",
                data=email_data,
            )
            log.info(f"Reschedule offer email enqueued for appointment #{appointment.id} to {client_email}")
        except Exception as e:
            log.error(f"Failed to enqueue reschedule offer email for appointment #{appointment.id}: {e}")

    log.info(f"Appointment #{appointment.id} marked as reschedule by Bot admin")
    return ProposeRescheduleResponse(
        success=True,
        message="Запись отменена, письмо с предложением отправлено",
        appointment_id=appointment.id,
    )
