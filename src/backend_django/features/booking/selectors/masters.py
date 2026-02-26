from core.cache import get_cached_data
from core.logger import log

from ..models import Master


class MasterSelector:
    """
    Selector for retrieving Master data.
    Uses Redis caching for performance.
    """

    @staticmethod
    def get_active_masters():
        """Returns active masters visible on the public site."""
        log.debug("Selector: MasterSelector | Action: GetActiveMasters")

        def fetch():
            log.debug("Selector: MasterSelector | Action: FetchDB | target=ActiveMasters")
            return list(Master.objects.filter(status=Master.STATUS_ACTIVE, is_public=True).order_by("order", "name"))

        return get_cached_data("active_masters_cache", fetch)

    @staticmethod
    def get_owner():
        """Returns the salon owner (first found), only if publicly visible."""
        log.debug("Selector: MasterSelector | Action: GetOwner")

        def fetch():
            log.debug("Selector: MasterSelector | Action: FetchDB | target=Owner")
            return Master.objects.filter(is_owner=True, status=Master.STATUS_ACTIVE, is_public=True).first()

        return get_cached_data("salon_owner_cache", fetch)

    @staticmethod
    def get_team_members():
        """Returns active public masters excluding the owner."""
        log.debug("Selector: MasterSelector | Action: GetTeamMembers")

        def fetch():
            log.debug("Selector: MasterSelector | Action: FetchDB | target=TeamMembers")
            return list(
                Master.objects.filter(status=Master.STATUS_ACTIVE, is_owner=False, is_public=True).order_by(
                    "order", "name"
                )
            )

        return get_cached_data("team_members_cache", fetch)

    @staticmethod
    def get_all_bookable_masters():
        """All active masters including hidden — for slot calculation and booking assignment."""
        log.debug("Selector: MasterSelector | Action: GetAllBookableMasters")
        return list(Master.objects.filter(status=Master.STATUS_ACTIVE).order_by("order", "name"))
