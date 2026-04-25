from __future__ import annotations

from typing import Any, Protocol


class CampaignDispatcher(Protocol):
    async def enqueue_batch(self, payload: dict[str, Any]) -> str: ...


class ArqCampaignDispatcher:
    """Enqueues batches of campaign recipients into arq."""

    async def enqueue_batch(self, payload: dict[str, Any]) -> str:
        from core.arq.client import DjangoArqClient

        job_id = await DjangoArqClient.aenqueue(
            "send_campaign_batch_task",
            payload=payload,
        )
        return str(job_id)
