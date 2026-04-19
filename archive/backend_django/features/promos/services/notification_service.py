"""Business logic for promo messages."""

from django.db.models import F, Q, QuerySet
from django.utils import timezone
from features.promos.models import PromoMessage


class PromoService:
    """Service for managing and displaying promo messages."""

    @staticmethod
    def get_active_promo(page_slug: str | None = None) -> PromoMessage | None:
        """
        Get the highest priority active promo for a specific page.

        Args:
            page_slug: Page identifier (e.g., 'home', 'services', 'team').
                      If None, returns promos targeting all pages.

        Returns:
            PromoMessage object or None if no active promo found.
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
    def track_view(promo_id: int) -> None:
        """
        Increment the views_count for a promo.

        Args:
            promo_id: ID of the promo to track.
        """
        PromoMessage.objects.filter(id=promo_id).update(views_count=F("views_count") + 1)

    @staticmethod
    def track_click(promo_id: int) -> None:
        """
        Increment the clicks_count for a promo.

        Args:
            promo_id: ID of the promo to track.
        """
        PromoMessage.objects.filter(id=promo_id).update(clicks_count=F("clicks_count") + 1)

    @staticmethod
    def is_promo_active(promo_id: int) -> bool:
        """
        Check if a promo is currently active.

        Args:
            promo_id: ID of the promo to check.

        Returns:
            True if promo is active and within date range, False otherwise.
        """
        try:
            promo = PromoMessage.objects.get(id=promo_id)
            return promo.is_currently_active
        except PromoMessage.DoesNotExist:
            return False
