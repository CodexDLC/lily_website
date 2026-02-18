from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

if TYPE_CHECKING:
    from src.shared.core.manager_redis.manager import StreamManager
    from src.workers.notification_worker.services.notification_service import NotificationService


async def send_email_task(
    ctx: dict[str, Any],
    recipient_email: str,
    subject: str,
    template_name: str,
    data: dict[str, Any],
):
    """
    Задача для отправки email через ARQ.
    """
    log.info(f"Sending email to {recipient_email} with subject '{subject}' using template '{template_name}'")

    notification_service = cast("NotificationService | None", ctx.get("notification_service"))
    appointment_id = data.get("id")

    if not notification_service:
        log.error("NotificationService not found in worker context!")
        await _send_status_update(ctx, appointment_id, "email", "failed")
        return

    try:
        await notification_service.send_notification(
            email=recipient_email, subject=subject, template_name=template_name, data=data
        )
        log.success(f"Email sent successfully to {recipient_email}")
        await _send_status_update(ctx, appointment_id, "email", "success")
    except Exception as e:
        log.error(f"Failed to send email to {recipient_email}: {e}", exc_info=True)
        await _send_status_update(ctx, appointment_id, "email", "failed")


async def _send_status_update(ctx: dict[str, Any], appointment_id: int | None, channel: str, status: str):
    """
    Отправка статуса обратно в Redis Stream.
    """
    if not appointment_id:
        return

    stream_manager = cast("StreamManager | None", ctx.get("stream_manager"))
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
