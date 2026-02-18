from typing import Any, cast

from loguru import logger as log


async def send_twilio_task(
    ctx: dict[str, Any],
    phone_number: str,
    message: str,
    appointment_id: int | None = None,
) -> None:
    """
    Задача для отправки сообщения через Twilio.
    Логика: Пробуем WhatsApp, если ошибка -> SMS.
    """
    log.info(f"Task: send_twilio_task | phone={phone_number} | appointment_id={appointment_id}")

    # Импортируем внутри, чтобы избежать циклов, если TYPE_CHECKING не хватает
    from src.workers.core.base_module.twilio_service import TwilioService

    twilio_service = cast(TwilioService | None, ctx.get("twilio_service"))
    if not twilio_service:
        log.error("TwilioService not found in context or not configured. Cannot send message.")
        await _send_status_update(ctx, appointment_id, "twilio", "failed")
        return

    # 1. Попытка отправить WhatsApp
    log.info(f"Attempting WhatsApp to {phone_number}")
    wa_success = twilio_service.send_whatsapp(phone_number, message)

    if wa_success:
        log.info("WhatsApp sent successfully.")
        await _send_status_update(ctx, appointment_id, "twilio", "success")
        return

    # 2. Фолбек на SMS
    log.warning(f"WhatsApp failed for {phone_number}. Falling back to SMS.")
    sms_success = twilio_service.send_sms(phone_number, message)

    if sms_success:
        log.info("Fallback SMS sent successfully.")
        await _send_status_update(ctx, appointment_id, "twilio", "success")
    else:
        log.error("Fallback SMS also failed.")
        await _send_status_update(ctx, appointment_id, "twilio", "failed")


async def send_appointment_notification(
    ctx: dict[str, Any],
    notification_data: dict[str, Any],
) -> None:
    """
    Диспетчер уведомлений.
    """
    appointment_id = notification_data.get("appointment_id")
    log.info(f"Task: send_appointment_notification | appointment_id={appointment_id}")

    from src.workers.core.base import ArqService

    arq_service = cast(ArqService | None, ctx.get("arq_service"))

    if not arq_service:
        log.error("ArqService not found in context. Cannot enqueue sub-tasks.")
        return

    # 1. Email Task
    email = notification_data.get("email")
    if email and email.lower() != "не указан":
        try:
            await arq_service.enqueue_job(
                "send_email_task",
                recipient_email=email,
                subject=notification_data.get("email_subject"),
                template_name=notification_data.get("email_template"),
                data=notification_data.get("email_data"),
            )
            log.info(f"Enqueued Email task for {email}")
        except Exception as e:
            log.error(f"Failed to enqueue Email task: {e}")
            await _send_status_update(ctx, appointment_id, "email", "failed")

    # 2. Twilio Task (SMS/WhatsApp)
    phone = notification_data.get("phone")
    sms_text = notification_data.get("sms_text")
    if phone and sms_text:
        try:
            await arq_service.enqueue_job(
                "send_twilio_task",
                phone_number=phone,
                message=sms_text,
                appointment_id=appointment_id,
            )
            log.info(f"Enqueued Twilio task for {phone}")
        except Exception as e:
            log.error(f"Failed to enqueue Twilio task: {e}")
            await _send_status_update(ctx, appointment_id, "twilio", "failed")


async def _send_status_update(ctx: dict[str, Any], appointment_id: int | None, channel: str, status: str):
    if not appointment_id:
        return

    from src.shared.core.manager_redis.manager import StreamManager

    stream_manager = cast(StreamManager | None, ctx.get("stream_manager"))

    if not stream_manager:
        log.warning("StreamManager not available for status update.")
        return

    payload = {
        "type": "notification_status",
        "appointment_id": appointment_id,
        "channel": channel,
        "status": status,
    }
    try:
        await stream_manager.add_event("bot_events", payload)
        log.info(f"Status update sent: {payload}")
    except Exception as e:
        log.error(f"Failed to send status update: {e}")
