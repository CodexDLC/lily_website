from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.workers.notification_worker.tasks.utils import send_status_update as _send_status_update

if TYPE_CHECKING:
    from src.workers.notification_worker.services.notification_service import NotificationService


async def send_email_task(
    ctx: dict[str, Any],
    recipient_email: str,
    subject: str,
    template_name: str,
    data: dict[str, Any],
):
    """
    Task for sending email via ARQ.
    """
    log.info(
        f"Task: send_email_task | Action: Start | recipient={recipient_email} | subject={subject} | template={template_name}"
    )

    notification_service = cast("NotificationService | None", ctx.get("notification_service"))
    appointment_id = data.get("id")

    if not notification_service:
        log.error("Task: send_email_task | Action: Failed | error=NotificationServiceMissing")
        await _send_status_update(ctx, appointment_id, "email", "failed")
        return

    try:
        await notification_service.send_notification(
            email=recipient_email, subject=subject, template_name=template_name, data=data
        )
        log.info(f"Task: send_email_task | Action: Success | recipient={recipient_email}")
        await _send_status_update(ctx, appointment_id, "email", "success")
    except Exception as e:
        log.error(f"Task: send_email_task | Action: Failed | recipient={recipient_email} | error={e}")
        await _send_status_update(ctx, appointment_id, "email", "failed")
