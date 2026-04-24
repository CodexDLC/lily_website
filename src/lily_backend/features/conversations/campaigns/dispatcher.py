from __future__ import annotations

from typing import Protocol


class CampaignDispatcher(Protocol):
    async def enqueue(self, campaign_id: int) -> str: ...


class ArqCampaignDispatcher:
    """Enqueues a single controlling send_campaign_task into arq."""

    async def enqueue(self, campaign_id: int) -> str:
        from core.arq.client import DjangoArqClient

        job_id = await DjangoArqClient.aenqueue(
            "send_campaign_task",
            payload={"campaign_id": campaign_id},
            queue_name="system",
            job_id=f"campaign:{campaign_id}",
        )
        return str(job_id)
