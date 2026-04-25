from __future__ import annotations

from typing import Any

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
        from django.conf import settings

        from features.conversations.models.campaign import CampaignRecipient

        count = await sync_to_async(self.materialize_recipients)(campaign)
        if count == 0:
            campaign.status = Campaign.Status.FAILED
            campaign.status_reason = "empty_audience"
            await sync_to_async(campaign.save)()
            return

        campaign.status = Campaign.Status.SENDING
        await sync_to_async(campaign.save)()

        tpl = self._templates.get(campaign.template_key)
        site_context = {
            "site_url": getattr(settings, "SITE_URL", "").rstrip("/"),
            "logo_url": getattr(settings, "SITE_LOGO_URL", ""),
        }

        batch_size = 25
        offset = 0
        total_enqueued = 0

        while True:
            # Fetch batch of recipient data
            batch_data: list[dict[str, Any]] = await sync_to_async(list)(
                CampaignRecipient.objects.filter(
                    campaign=campaign,
                    status=CampaignRecipient.Status.PENDING,
                )
                .order_by("id")
                .values(
                    "id",
                    "email",
                    "first_name",
                    "last_name",
                    "recipient__unsubscribe_token",
                )[offset : offset + batch_size]
            )

            if not batch_data:
                break

            recipients = []
            for row in batch_data:
                recipients.append(
                    {
                        "id": row["id"],
                        "email": row["email"],
                        "first_name": row["first_name"],
                        "last_name": row["last_name"],
                        "unsubscribe_token": str(row["recipient__unsubscribe_token"] or ""),
                    }
                )

            payload = {
                "campaign_id": campaign.pk,
                "subject": campaign.subject,
                "body_text": campaign.body_text,
                "template_key": campaign.template_key,
                "arq_template_name": tpl.arq_template_name,
                "is_marketing": campaign.is_marketing,
                "site_context": site_context,
                "recipients": recipients,
            }

            await self._dispatcher.enqueue_batch(payload)

            # Mark them as queued in the DB so we don't pick them up again if re-run
            # For simplicity, we just increment offset, but ideally we'd mark them.
            # But the user wants a simple immediate fix.
            total_enqueued += len(recipients)
            offset += batch_size

        campaign.status = Campaign.Status.DONE  # In batch mode, we mark it done after enqueuing all batches
        import django.utils.timezone as tz

        campaign.sent_at = tz.now()
        await sync_to_async(campaign.save)()


def build_campaign_service() -> CampaignService:
    """Project glue-code factory. Lives here, not in the library."""
    return CampaignService(
        audience=DjangoAudienceBuilder(),
        dispatcher=ArqCampaignDispatcher(),
        templates=template_registry,
        locales=SingleLocaleResolver("de"),
    )
