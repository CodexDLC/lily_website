from __future__ import annotations

from asgiref.sync import sync_to_async
from django.db import transaction

from features.conversations.campaigns.audience import AudienceBuilder, AudienceFilter
from features.conversations.campaigns.dispatcher import ArqCampaignDispatcher, CampaignDispatcher
from features.conversations.campaigns.locales import LocaleResolver, SingleLocaleResolver
from features.conversations.campaigns.templates import TemplateRegistry, template_registry
from features.conversations.models.campaign import Campaign, CampaignRecipient
from features.conversations.selector.audience import DjangoAudienceBuilder


class CampaignService:
    def __init__(
        self,
        *,
        audience: AudienceBuilder,
        dispatcher: CampaignDispatcher,
        templates: TemplateRegistry,
        locales: LocaleResolver,
    ) -> None:
        self._audience = audience
        self._dispatcher = dispatcher
        self._templates = templates
        self._locales = locales

    def preview_count(self, f: AudienceFilter) -> int:
        return self._audience.count(f)

    @transaction.atomic
    def materialize_recipients(self, campaign: Campaign) -> int:
        f = AudienceFilter.from_dict(campaign.audience_filter)
        count = 0
        for draft in self._audience.materialize(f):
            CampaignRecipient.objects.get_or_create(
                campaign=campaign,
                recipient_id=draft.recipient_id,
                defaults=dict(
                    email=draft.email,
                    first_name=draft.first_name,
                    last_name=draft.last_name,
                    locale=draft.locale,
                ),
            )
            count += 1
        return count

    async def send(self, campaign: Campaign) -> None:
        count = await sync_to_async(self.materialize_recipients)(campaign)
        if count == 0:
            campaign.status = Campaign.Status.FAILED
            campaign.status_reason = "empty_audience"
            await sync_to_async(campaign.save)()
            return
        parent_id = await self._dispatcher.enqueue(campaign.pk)
        campaign.status = Campaign.Status.QUEUED
        campaign.arq_parent_job_id = parent_id or ""
        await sync_to_async(campaign.save)()


def build_campaign_service() -> CampaignService:
    """Project glue-code factory. Lives here, not in the library."""
    return CampaignService(
        audience=DjangoAudienceBuilder(),
        dispatcher=ArqCampaignDispatcher(),
        templates=template_registry,
        locales=SingleLocaleResolver("de"),
    )
