from unittest.mock import AsyncMock, MagicMock

import pytest

from src.workers.notification_worker.tasks.campaign_tasks import (
    _build_unsubscribe_url,
    _fetch_batch,
    _mark_done,
    _mark_failed,
    _mark_sending,
    send_campaign_task,
)


@pytest.fixture
def mock_ctx():
    return {
        "arq_pool": MagicMock(enqueue_job=AsyncMock()),
    }


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_campaign_task_missing_id(mock_ctx):
    await send_campaign_task(mock_ctx, payload={})
    # Should log error and return silently


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_campaign_task_not_found(mock_ctx):
    await send_campaign_task(mock_ctx, payload={"campaign_id": 9999})
    # Should log error and return


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_campaign_task_success(mock_ctx):
    import uuid

    from asgiref.sync import sync_to_async
    from features.conversations.models.campaign import Campaign, CampaignRecipient
    from system.models import Client

    client = await sync_to_async(Client.objects.create)(email="task_test@example.com", unsubscribe_token=uuid.uuid4())
    campaign = await sync_to_async(Campaign.objects.create)(
        subject="Hello",
        body_text="Test body",
        template_key="basic",
        status=Campaign.Status.DRAFT,
    )
    await sync_to_async(CampaignRecipient.objects.create)(
        campaign=campaign,
        recipient=client,
        email=client.email,
        first_name="Anna",
        last_name="L",
        status=CampaignRecipient.Status.PENDING,
    )

    await send_campaign_task(mock_ctx, payload={"campaign_id": campaign.id})

    await sync_to_async(campaign.refresh_from_db)()
    assert campaign.status == Campaign.Status.DONE
    assert campaign.sent_at is not None
    assert mock_ctx["arq_pool"].enqueue_job.called

    # Verify recipient updated with job id
    rec = await sync_to_async(campaign.recipients.first)()
    assert rec.arq_job_id != ""


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_campaign_task_unknown_template(mock_ctx):
    from asgiref.sync import sync_to_async
    from features.conversations.models.campaign import Campaign

    campaign = await sync_to_async(Campaign.objects.create)(
        subject="Test",
        template_key="non_existent",
    )
    await send_campaign_task(mock_ctx, payload={"campaign_id": campaign.id})

    await sync_to_async(campaign.refresh_from_db)()
    assert campaign.status == Campaign.Status.FAILED
    assert "unknown_template" in campaign.status_reason


def test_build_unsubscribe_url(settings):
    settings.SITE_URL = "https://example.com"
    assert _build_unsubscribe_url("abc") == "https://example.com/u/abc/"


@pytest.mark.django_db
def test_helpers():
    from features.conversations.models.campaign import Campaign

    campaign = Campaign.objects.create(subject="T")

    _mark_sending(campaign)
    assert campaign.status == Campaign.Status.SENDING

    _mark_done(campaign)
    assert campaign.status == Campaign.Status.DONE

    _mark_failed(campaign, "error")
    assert campaign.status == Campaign.Status.FAILED
    assert campaign.status_reason == "error"


@pytest.mark.django_db
def test_fetch_batch():
    from features.conversations.models.campaign import Campaign, CampaignRecipient
    from system.models import Client

    client = Client.objects.create(email="batch_test@example.com")
    c = Campaign.objects.create(subject="T")
    CampaignRecipient.objects.create(campaign=c, recipient=client, email="batch_test@example.com")

    batch = _fetch_batch(c.id, 0, 10)
    assert len(batch) == 1
    assert batch[0]["email"] == "batch_test@example.com"
