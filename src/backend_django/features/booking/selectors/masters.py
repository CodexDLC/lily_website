from ..models import Master


class MasterSelector:
    """Selector for retrieving Master data."""

    @staticmethod
    def get_active_masters():
        """Returns all active masters."""
        return Master.objects.filter(status=Master.STATUS_ACTIVE).order_by("order", "name")

    @staticmethod
    def get_owner():
        """Returns the salon owner (first found)."""
        return Master.objects.filter(is_owner=True, status=Master.STATUS_ACTIVE).first()

    @staticmethod
    def get_team_members():
        """Returns active masters excluding the owner."""
        return Master.objects.filter(status=Master.STATUS_ACTIVE, is_owner=False).order_by("order", "name")
