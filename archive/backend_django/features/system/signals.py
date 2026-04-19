from core.logger import log
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from features.main.models.contact_request import ContactRequest

from .redis_managers.admin_dashboard_manager import AdminDashboardManager


@receiver(post_save, sender=ContactRequest)
@receiver(post_delete, sender=ContactRequest)
def invalidate_dashboard_cache(sender, instance, **kwargs):
    """
    Clears the admin dashboard cache when a ContactRequest
    is created, updated, or deleted.
    The bot will re-trigger a refresh on its next request.
    """
    log.debug(f"Signal: ContactRequest | Action: InvalidateCache | request_id={instance.id}")
    try:
        AdminDashboardManager.clear_cache("contacts")
        log.info(f"Signal: ContactRequest | Action: Success | request_id={instance.id} | target=AdminDashboard")
    except Exception as e:
        log.error(f"Signal: ContactRequest | Action: Failed | request_id={instance.id} | error={e}")
