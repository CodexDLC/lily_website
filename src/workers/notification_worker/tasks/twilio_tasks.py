import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.shared.utils.text import transliterate

from .utils import send_status_update as _send_status_update

if TYPE_CHECKING:
    from src.shared.core.redis_service import RedisService
    from src.workers.core.base import ArqService
    from src.workers.core.base_module.twilio_service import TwilioService
    from src.workers.core.config import WorkerSettings
    from src.workers.notification_worker.services.notification_service import NotificationService


async def send_twilio_task(
    ctx: dict[str, Any],
    phone_number: str,
    message: str,
    appointment_id: int | None = None,
    media_url: str | None = None,
    variables: dict[str, str] | None = None,
) -> None:
    """
    Задача для отправки сообщения через Twilio.
    Логика: WhatsApp Template (без медиа) -> WhatsApp Free (с медиа) -> SMS.
    """
    twilio_service = cast("TwilioService | None", ctx.get("twilio_service"))
    settings = cast("WorkerSettings | None", ctx.get("settings"))

    if not twilio_service:
        log.error("TwilioService not found.")
        await _send_status_update(ctx, appointment_id, "twilio", "failed")
        return

    # 1. Попытка отправить WhatsApp Template
    if variables and settings and settings.TWILIO_WHATSAPP_TEMPLATE_SID:
        log.info(f"Attempting WhatsApp Template {settings.TWILIO_WHATSAPP_TEMPLATE_SID} to {phone_number}")
        wa_success = twilio_service.send_whatsapp_template(
            to_number=phone_number, content_sid=settings.TWILIO_WHATSAPP_TEMPLATE_SID, variables=variables
        )
        if wa_success:
            log.info("WhatsApp Template sent successfully.")
            await _send_status_update(ctx, appointment_id, "twilio", "success")
            return

    # 2. Попытка отправить обычный WhatsApp
    log.info(f"Attempting Free-form WhatsApp to {phone_number}")
    wa_success = twilio_service.send_whatsapp(phone_number, message, media_url=media_url)
    if wa_success:
        log.info("Free-form WhatsApp sent successfully.")
        await _send_status_update(ctx, appointment_id, "twilio", "success")
        return

    # 3. Фолбек на SMS
    log.warning("WhatsApp failed. Falling back to SMS.")
    sms_success = twilio_service.send_sms(phone_number, message)
    if sms_success:
        log.info("Fallback SMS sent successfully.")
        await _send_status_update(ctx, appointment_id, "twilio", "success")
    else:
        log.error("Fallback SMS also failed.")
        await _send_status_update(ctx, appointment_id, "twilio", "failed")


async def send_appointment_notification(
    ctx: dict[str, Any],
    appointment_id: int,
    status: str,
    reason_text: str | None = None,
) -> None:
    """Автономный диспетчер уведомлений."""
    redis_service = cast("RedisService | None", ctx.get("redis_service"))
    if not redis_service:
        return

    cache_key = f"notifications:cache:{appointment_id}"
    raw_data = await redis_service.get_value(cache_key)

    if not raw_data:
        log.warning(f"No data in Redis for appointment {appointment_id}. Skipping.")
        return

    try:
        appointment_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except Exception as e:
        log.error(f"Failed to parse JSON from Redis for {appointment_id}: {e}")
        return

    arq_service = cast("ArqService | None", ctx.get("arq_service"))
    notification_service = cast("NotificationService | None", ctx.get("notification_service"))

    if not arq_service or not notification_service:
        return

    # Email...
    email = appointment_data.get("client_email")
    if email and email.lower() != "не указан":
        await arq_service.enqueue_job(
            "send_email_task",
            recipient_email=email,
            subject="Terminbestätigung - Lily Beauty Salon",
            template_name="confirmation.html" if status == "confirmed" else "cancellation.html",
            data=appointment_data,
        )

    # Twilio (WhatsApp/SMS)...
    phone = appointment_data.get("client_phone")
    if status == "confirmed" and phone:
        dt_str = str(appointment_data.get("datetime", ""))
        try:
            dt_obj = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            date = dt_obj.strftime("%d.%m.%Y")
            time = dt_obj.strftime("%H:%M")
        except Exception:
            parts = dt_str.split(" ")
            date = parts[0] if len(parts) > 0 else dt_str
            time = parts[1] if len(parts) > 1 else ""

        template_vars = {
            "1": transliterate(appointment_data.get("first_name", "Guest")),
            "2": date,
            "3": time,
            "4": str(appointment_id),
        }

        sms_text = notification_service.get_sms_text(appointment_data)
        logo_url = notification_service.get_absolute_logo_url()

        await arq_service.enqueue_job(
            "send_twilio_task",
            phone_number=phone,
            message=sms_text,
            appointment_id=appointment_id,
            variables=template_vars,
            media_url=logo_url,
        )
