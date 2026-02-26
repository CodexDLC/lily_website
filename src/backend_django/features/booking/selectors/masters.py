from core.cache import get_cached_data

from ..models import Master


class MasterSelector:
    """
    Selector for retrieving Master data.
    Uses Redis caching for performance.
    """

    @staticmethod
    def get_active_masters():
        """Returns active masters visible on the public site."""

        def fetch():
            return list(Master.objects.filter(status=Master.STATUS_ACTIVE, is_public=True).order_by("order", "name"))

        return get_cached_data("active_masters_cache", fetch)

    @staticmethod
    def get_owner():
        """Returns the salon owner (first found), only if publicly visible."""

        def fetch():
            return Master.objects.filter(is_owner=True, status=Master.STATUS_ACTIVE, is_public=True).first()

        return get_cached_data("salon_owner_cache", fetch)

    @staticmethod
    def get_team_members():
        """Returns active public masters excluding the owner."""

        def fetch():
            return list(
                Master.objects.filter(status=Master.STATUS_ACTIVE, is_owner=False, is_public=True).order_by(
                    "order", "name"
                )
            )

        return get_cached_data("team_members_cache", fetch)

    @staticmethod
    def get_all_bookable_masters():
        """All active masters including hidden — for slot calculation and booking assignment."""
        return list(Master.objects.filter(status=Master.STATUS_ACTIVE).order_by("order", "name"))
