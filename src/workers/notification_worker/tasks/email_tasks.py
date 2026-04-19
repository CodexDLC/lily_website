from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.workers.notification_worker.tasks.utils import send_status_update as _send_status_update

if TYPE_CHECKING:
    from src.workers.core.base_module.orchestrator import NotificationOrchestrator
    from src.workers.notification_worker.services.notification_service import NotificationService


async def send_email_task(
    ctx: dict[str, Any],
    recipient_email: str,
    subject: str,
    template_name: str,
    data: dict[str, Any],
    appointment_id: int | None = None,
) -> None:
    """
    Task to send email using the Orchestrator (SMTP with fallback).
    Renders the template first.
    """
    log.info(f"Task: send_email_task | Action: Start | to={recipient_email} | template={template_name}")

    notification_service = cast("NotificationService | None", ctx.get("notification_service"))
    orchestrator = cast("NotificationOrchestrator | None", ctx.get("orchestrator"))

    if not notification_service or not orchestrator:
        log.error("Task: send_email_task | Action: Failed | error=ServicesMissing")
        await _send_status_update(ctx, appointment_id, "email", "failed", template_name=template_name)
        return

    try:
        # 1. Prepare data (Templating logic remains here or in service)
        full_context = notification_service.enrich_email_context(data)
        html_content = notification_service.renderer.render(template_name, full_context)

        # 2. Send via Orchestrator
        success = await orchestrator.send_email(
            to_email=recipient_email,
            subject=subject,
            html_content=html_content,
            headers=_mailbox_headers(data),
        )

        if success:
            log.info(f"Task: send_email_task | Action: Success | to={recipient_email}")
            await _send_status_update(ctx, appointment_id, "email", "success", template_name=template_name)
        else:
            log.error(f"Task: send_email_task | Action: Failed | to={recipient_email}")
            await _send_status_update(ctx, appointment_id, "email", "failed", template_name=template_name)

    except Exception as e:
        log.exception(f"Task: send_email_task | Action: Error | to={recipient_email} | error={e}")
        await _send_status_update(ctx, appointment_id, "email", "failed", template_name=template_name)
        raise


def _mailbox_headers(data: dict[str, Any]) -> dict[str, str] | None:
    thread_key = data.get("thread_key") or data.get("reply_match_token")
    if not thread_key:
        return None
    clean_key = str(thread_key).strip()
    return {
        "X-Lily-Thread-Key": clean_key,
        "Message-ID": f"<{clean_key}>",
        "References": f"<{clean_key}>",
        "In-Reply-To": f"<{clean_key}>",
    }
