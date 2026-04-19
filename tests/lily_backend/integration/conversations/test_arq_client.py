from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from core.arq.client import DjangoArqClient, arq_client


@pytest.mark.asyncio
async def test_aenqueue_uses_enqueue_job_payload_contract(monkeypatch):
    pool = SimpleNamespace(enqueue_job=AsyncMock(return_value=SimpleNamespace(job_id="job-123")))

    async def fake_get_pool():
        return pool

    monkeypatch.setattr(DjangoArqClient, "get_pool", fake_get_pool)

    result = await DjangoArqClient.aenqueue("send_notification_task", {"recipient_email": "client@example.com"})

    assert result == "job-123"
    pool.enqueue_job.assert_awaited_once_with(
        "send_notification_task",
        payload={"recipient_email": "client@example.com"},
    )


def test_sync_enqueue_and_module_alias_match_notification_expectations(monkeypatch):
    async_enqueue = AsyncMock(return_value="job-456")
    monkeypatch.setattr(DjangoArqClient, "aenqueue", async_enqueue)

    result = DjangoArqClient.enqueue("send_notification_task", {"payload": True})

    assert result == "job-456"
    async_enqueue.assert_awaited_once_with("send_notification_task", {"payload": True})
    assert arq_client is DjangoArqClient
