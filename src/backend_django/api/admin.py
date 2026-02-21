from django.conf import settings
from features.system.services.dashboard_refresh_service import DashboardRefreshService
from loguru import logger as log
from ninja import Router
from ninja.security import APIKeyHeader


class BotApiKey(APIKeyHeader):
    """
    X-API-Key authentication for Telegram Bot.
    """

    param_name = "X-API-Key"

    def authenticate(self, request, key):
        expected_key = getattr(settings, "BOT_API_KEY", None)
        if expected_key and key == expected_key:
            return key
        return None


router = Router(auth=BotApiKey())


@router.post("/cache/refresh/")
async def refresh_dashboard_cache(request):
    """
    Triggers a full refresh of admin dashboard data in Redis.
    """
    try:
        await DashboardRefreshService.refresh_all()
        log.info("AdminAPI | Web dashboard cache refreshed successfully")
        return {"success": True, "message": "Cache refreshed"}
    except Exception as e:
        log.error(f"AdminAPI | Error refreshing cache: {e}")
        return {"success": False, "message": str(e)}


@router.post("/contacts/{contact_id}/process/")
async def process_contact(request, contact_id: int):
    """
    Marks a contact request as processed and refreshes cache.
    """
    from features.main.models.contact_request import ContactRequest

    try:
        contact = await ContactRequest.objects.filter(id=contact_id).afirst()
        if not contact:
            return {"success": False, "message": "Contact not found"}

        contact.is_processed = True
        await contact.asave()

        # Trigger full refresh to update Redis (signals will also catch this, but better be safe)
        await DashboardRefreshService.refresh_all()

        log.info(f"AdminAPI | Contact {contact_id} marked as processed")
        return {"success": True, "message": "Contact processed"}
    except Exception as e:
        log.error(f"AdminAPI | Error processing contact {contact_id}: {e}")
        return {"success": False, "message": str(e)}
