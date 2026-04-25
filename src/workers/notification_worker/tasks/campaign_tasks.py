from __future__ import annotations

from typing import Any

from loguru import logger as log


async def send_campaign_batch_task(
    ctx: dict[str, Any],
    payload: dict[str, Any] | None = None,
) -> None:
    """
    Independent batch task: receives pre-prepared data from Django
    and enqueues individual send_universal_notification_task for each recipient.
    No Django models imported.
    """
    if not payload:
        log.error("send_campaign_batch_task: missing payload")
        return

    campaign_id = payload.get("campaign_id")
    subject = payload.get("subject")
    body_text = payload.get("body_text")
    arq_template_name = payload.get("arq_template_name")
    is_marketing = payload.get("is_marketing", True)
    site_context = payload.get("site_context", {})
    recipients = payload.get("recipients", [])

    if not recipients:
        log.warning(f"send_campaign_batch_task: campaign {campaign_id} batch is empty")
        return

    pool = ctx.get("arq_pool") or ctx.get("redis")
    if pool is None:
        log.error("send_campaign_batch_task: no arq_pool/redis in context")
        return

    site_url = str(site_context.get("site_url", "")).rstrip("/")

    for row in recipients:
        token = row.get("unsubscribe_token", "")
        unsubscribe_url = f"{site_url}/u/{token}/" if token else ""

        # Prepare context for the universal task
        context_data = {
            "body_text": body_text,
            "subject": subject,
            "name": row.get("first_name", ""),
            "unsubscribe_url": unsubscribe_url,
            "is_marketing": is_marketing,
            **site_context,
        }

        try:
            await pool.enqueue_job(
                "send_universal_notification_task",
                payload={
                    "notification_id": f"campaign_{campaign_id}_{row['id']}",
                    "recipient": {
                        "email": row["email"],
                        "first_name": row["first_name"],
                        "last_name": row["last_name"],
                        "phone": None,
                    },
                    "template_name": arq_template_name,
                    "subject": subject,
                    "channels": ["email"],
                    "context_data": context_data,
                },
            )
        except Exception as exc:
            log.error(f"send_campaign_batch_task: enqueue failed for recipient {row['id']}: {exc}")

    log.info(f"send_campaign_batch_task: campaign {campaign_id} batch of {len(recipients)} recipients queued")
