"""Business logic for promo promos."""

from django.db.models import F, Q, QuerySet
from django.utils import timezone
from features.promos.models import PromoMessage


class NotificationService:
    """Service for managing and displaying promo promos."""

    @staticmethod
    def get_active_notification(page_slug: str | None = None) -> PromoMessage | None:
        """
        Get the highest priority active notification for a specific page.

        Args:
            page_slug: Page identifier (e.g., 'home', 'services', 'team').
                      If None, returns promos targeting all pages.

        Returns:
            PromoMessage object or None if no active notification found.
        """
        now = timezone.now()

        # Base queryset: active promos within date range
        queryset = PromoMessage.objects.filter(
            is_active=True,
            starts_at__lte=now,
            ends_at__gte=now,
        )

        # Filter by target pages
        if page_slug:
            # Get promos for all pages OR specific page
            queryset = queryset.filter(Q(target_pages="") | Q(target_pages__icontains=page_slug))
        else:
            # Only get promos targeting all pages
            queryset = queryset.filter(target_pages="")

        # Order by priority (highest first) and start date (newest first)
        queryset = queryset.order_by("-priority", "-starts_at")

        # Return the first match (highest priority)
        return queryset.first()

    @staticmethod
    def get_all_active_promos(page_slug: str | None = None) -> QuerySet[PromoMessage]:
        """
        Get all active promos for a specific page.

        Args:
            page_slug: Page identifier. If None, returns promos targeting all pages.

        Returns:
            QuerySet of active PromoMessage objects.
        """
        now = timezone.now()

        queryset = PromoMessage.objects.filter(
            is_active=True,
            starts_at__lte=now,
            ends_at__gte=now,
        )

        if page_slug:
            queryset = queryset.filter(Q(target_pages="") | Q(target_pages__icontains=page_slug))
        else:
            queryset = queryset.filter(target_pages="")

        return queryset.order_by("-priority", "-starts_at")

    @staticmethod
    def track_view(notification_id: int) -> None:
        """
        Increment the views_count for a notification.

        Args:
            notification_id: ID of the notification to track.
        """
        PromoMessage.objects.filter(id=notification_id).update(views_count=F("views_count") + 1)

    @staticmethod
    def track_click(notification_id: int) -> None:
        """
        Increment the clicks_count for a notification.

        Args:
            notification_id: ID of the notification to track.
        """
        PromoMessage.objects.filter(id=notification_id).update(clicks_count=F("clicks_count") + 1)

    @staticmethod
    def is_notification_active(notification_id: int) -> bool:
        """
        Check if a notification is currently active.

        Args:
            notification_id: ID of the notification to check.

        Returns:
            True if notification is active and within date range, False otherwise.
        """
        try:
            notification = PromoMessage.objects.get(id=notification_id)
            return notification.is_currently_active
        except PromoMessage.DoesNotExist:
            return False
