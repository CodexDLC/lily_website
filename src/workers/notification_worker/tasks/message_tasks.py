from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.shared.utils.transliteration import transliterate
from src.workers.notification_worker.tasks.utils import send_status_update as _send_status_update

if TYPE_CHECKING:
    from src.workers.core.base import ArqService
    from src.workers.core.base_module.orchestrator import NotificationOrchestrator
    from src.workers.notification_worker.config import WorkerSettings
    from src.workers.notification_worker.services.notification_service import NotificationService


async def send_message_task(
    ctx: dict[str, Any],
    phone_number: str,
    message: str,
    appointment_id: int | None = None,
    media_url: str | None = None,
    variables: dict[str, str] | None = None,
) -> None:
    """
    Task for sending a message using the Orchestrator (Seven.io -> Twilio fallback).
    """
    log.info(f"Task: send_message_task | Action: Start | phone={phone_number} | appt_id={appointment_id}")

    orchestrator = cast("NotificationOrchestrator | None", ctx.get("orchestrator"))
    settings = cast("WorkerSettings | None", ctx.get("settings"))

    if not orchestrator:
        log.error("Task: send_message_task | Action: Failed | error=OrchestratorMissing")
        await _send_status_update(ctx, appointment_id, "twilio", "failed")  # Still use 'twilio' status key for now
        return

    try:
        success = await orchestrator.send_message(
            to_number=phone_number,
            text=message,
            media_url=media_url,
            wa_template_sid=settings.TWILIO_WHATSAPP_TEMPLATE_SID if settings else None,
            wa_variables=variables,
        )

        if success:
            log.info(f"Task: send_message_task | Action: Success | phone={phone_number}")
            await _send_status_update(ctx, appointment_id, "twilio", "success")
        else:
            log.error(f"Task: send_message_task | Action: Failed | phone={phone_number}")
            await _send_status_update(ctx, appointment_id, "twilio", "failed")

    except Exception as e:
        log.exception(f"Task: send_message_task | Action: Error | phone={phone_number} | error={e}")
        await _send_status_update(ctx, appointment_id, "twilio", "failed")


async def send_appointment_notification(
    ctx: dict[str, Any], status: str, appointment_id: int, appointment_data: dict[str, Any]
) -> None:
    """
    Orchestrates sending email and message (WA/SMS) notifications for an appointment.
    """
    log.info(f"Task: send_appointment_notification | Action: Start | id={appointment_id} | status={status}")

    arq_service = cast("ArqService", ctx["arq_service"])
    notification_service = cast("NotificationService", ctx["notification_service"])

    # 1. Email Notification
    email = appointment_data.get("client_email")
    if email:
        log.debug(f"Task: send_appointment_notification | Action: EnqueueEmail | to={email}")
        subject = f"Appointment {status.capitalize()} - Lily Beauty"
        template = f"appointment_{status}.html"

        await arq_service.enqueue_job(
            "send_email_task",
            recipient_email=email,
            subject=subject,
            template_name=template,
            data=appointment_data,
            appointment_id=appointment_id,
        )

    # 2. Message Notification (WhatsApp/SMS)
    phone = appointment_data.get("client_phone")
    if phone:
        log.debug(f"Task: send_appointment_notification | Action: EnqueueMessage | phone={phone}")

        # Prepare content for the task
        dt_str = str(appointment_data.get("datetime", ""))
        try:
            dt_obj = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            date = dt_obj.strftime("%d.%m.%Y")
            time = dt_obj.strftime("%H:%M")
        except (ValueError, TypeError):
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
            "send_message_task",
            phone_number=phone,
            message=sms_text,
            appointment_id=appointment_id,
            media_url=logo_url,
            variables=template_vars,
        )

    log.info(f"Task: send_appointment_notification | Action: Success | appt_id={appointment_id}")
