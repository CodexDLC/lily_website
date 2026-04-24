from __future__ import annotations

import asyncio
from typing import Any

from django.conf import settings
from loguru import logger as log


def _mark_sending(campaign) -> None:
    from features.conversations.models.campaign import Campaign

    campaign.status = Campaign.Status.SENDING
    campaign.save(update_fields=["status"])


def _mark_done(campaign) -> None:
    from django.utils import timezone
    from features.conversations.models.campaign import Campaign

    campaign.status = Campaign.Status.DONE
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=["status", "sent_at"])


def _mark_failed(campaign, reason: str) -> None:
    from features.conversations.models.campaign import Campaign

    campaign.status = Campaign.Status.FAILED
    campaign.status_reason = reason
    campaign.save(update_fields=["status", "status_reason"])


def _mark_recipient_queued(recipient_id: int, job_id: str) -> None:
    from features.conversations.models.campaign import CampaignRecipient

    CampaignRecipient.objects.filter(pk=recipient_id).update(arq_job_id=job_id)


def _fetch_batch(campaign_id: int, offset: int, limit: int) -> list[dict]:
    from features.conversations.models.campaign import CampaignRecipient

    return list(
        CampaignRecipient.objects.filter(
            campaign_id=campaign_id,
            status=CampaignRecipient.Status.PENDING,
        )
        .order_by("id")
        .values(
            "id",
            "email",
            "first_name",
            "last_name",
            "locale",
            "recipient__unsubscribe_token",
        )[offset : offset + limit]
    )


def _build_unsubscribe_url(unsubscribe_token: str) -> str:
    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    return f"{site_url}/u/{unsubscribe_token}/"


async def send_campaign_task(
    ctx: dict[str, Any],
    payload: dict[str, Any] | None = None,
) -> None:
    """
    Parent task: reads CampaignRecipient in batches and enqueues
    send_universal_notification_task for each recipient.
    """
    campaign_id = (payload or {}).get("campaign_id")
    if not campaign_id:
        log.error("send_campaign_task: missing campaign_id in payload")
        return

    from asgiref.sync import sync_to_async
    from features.conversations.campaigns.templates import template_registry
    from features.conversations.models.campaign import Campaign

    try:
        campaign = await sync_to_async(Campaign.objects.get)(pk=campaign_id)
    except Campaign.DoesNotExist:
        log.error(f"send_campaign_task: Campaign {campaign_id} not found")
        return

    await sync_to_async(_mark_sending)(campaign)

    try:
        tpl = template_registry.get(campaign.template_key)
    except KeyError:
        await sync_to_async(_mark_failed)(campaign, f"unknown_template:{campaign.template_key}")
        return

    pool = ctx.get("arq_pool") or ctx.get("redis")

    batch_size = 50
    batch_sleep = 1.0

    offset = 0
    total = 0
    while True:
        batch = await sync_to_async(_fetch_batch)(campaign_id, offset, batch_size)
        if not batch:
            break

        for row in batch:
            token = str(row.get("recipient__unsubscribe_token") or "")
            context_data = tpl.build_context(
                body_text=campaign.body_text,
                extra={
                    "subject": campaign.subject,
                    "name": row["first_name"],
                    "unsubscribe_url": _build_unsubscribe_url(token),
                },
            )
            job = None
            if pool is not None:
                try:
                    job = await pool.enqueue_job(
                        "send_universal_notification_task",
                        payload={
                            "notification_id": f"campaign_{campaign_id}_{row['id']}",
                            "recipient": {
                                "email": row["email"],
                                "first_name": row["first_name"],
                                "last_name": row["last_name"],
                                "phone": None,
                            },
                            "template_name": tpl.arq_template_name,
                            "subject": campaign.subject,
                            "channels": ["email"],
                            "context_data": context_data,
                        },
                        _queue_name="system",
                    )
                except Exception as exc:
                    log.error(f"send_campaign_task: enqueue failed for recipient {row['id']}: {exc}")

            job_id = str(job.job_id) if job and hasattr(job, "job_id") else ""
            await sync_to_async(_mark_recipient_queued)(row["id"], job_id)
            total += 1

        offset += batch_size
        await asyncio.sleep(batch_sleep)

    log.info(f"send_campaign_task: campaign {campaign_id} done, {total} recipients queued")
    await sync_to_async(_mark_done)(campaign)
