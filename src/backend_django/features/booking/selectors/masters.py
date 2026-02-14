from core.cache import get_cached_data

from ..models import Master


class MasterSelector:
    """
    Selector for retrieving Master data.
    Uses Redis caching for performance.
    """

    @staticmethod
    def get_active_masters():
        """Returns all active masters."""

        def fetch():
            return list(Master.objects.filter(status=Master.STATUS_ACTIVE).order_by("order", "name"))

        return get_cached_data("active_masters_cache", fetch)

    @staticmethod
    def get_owner():
        """Returns the salon owner (first found)."""

        def fetch():
            return Master.objects.filter(is_owner=True, status=Master.STATUS_ACTIVE).first()

        return get_cached_data("salon_owner_cache", fetch)

    @staticmethod
    def get_team_members():
        """Returns active masters excluding the owner."""

        def fetch():
            return list(Master.objects.filter(status=Master.STATUS_ACTIVE, is_owner=False).order_by("order", "name"))

        return get_cached_data("team_members_cache", fetch)
