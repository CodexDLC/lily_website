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
    AdminDashboardManager.clear_cache("contacts")
