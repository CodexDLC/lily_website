from __future__ import annotations

from django.utils import timezone
from ninja import Router, Schema
from system.api.auth import require_internal_scope

from features.conversations.models.campaign import CampaignRecipient

router = Router(tags=["Campaigns"])


class RecipientStatusPayload(Schema):
    notification_id: str
    status: str  # "sent" | "failed"
    error: str = ""


@router.post("/recipient-status", summary="Update campaign recipient delivery status")
def update_recipient_status(request, payload: RecipientStatusPayload) -> dict:
    require_internal_scope(request, "campaigns.worker")

    # notification_id format: "campaign_{campaign_id}_{recipient_pk}"
    parts = payload.notification_id.split("_")
    if len(parts) != 3 or parts[0] != "campaign":
        return {"ok": False, "error": "invalid notification_id format"}

    try:
        recipient_pk = int(parts[2])
    except ValueError:
        return {"ok": False, "error": "invalid recipient pk"}

    updated = CampaignRecipient.objects.filter(pk=recipient_pk).update(
        status=payload.status,
        sent_at=timezone.now() if payload.status == CampaignRecipient.Status.SENT else None,
        error=payload.error,
    )

    return {"ok": bool(updated)}
