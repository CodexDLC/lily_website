from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from features.booking.models import Master


class CabinetAccessMixin(LoginRequiredMixin):
    """
    Base mixin for all cabinet views.
    Ensures user is logged in.
    """

    pass


class HtmxCabinetMixin:
    """
    Mixin for HTMX views in cabinet.
    """

    pass


class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin that ensures the user is an admin (staff or superuser).
    """

    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)


class MasterRequiredMixin(LoginRequiredMixin):
    """
    Mixin that ensures the user is logged in AND is a Master.
    If user is not a master, redirects to home or raises 403.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Check if user has a linked Master profile
        if not hasattr(request.user, "master_profile"):
            # If user is staff/superuser, maybe allow or redirect to admin?
            if request.user.is_staff:
                return super().dispatch(request, *args, **kwargs)

            # Regular user without master profile -> 403 or redirect
            raise PermissionDenied("You do not have a Master profile.")

        # Check if master is active (optional)
        master = request.user.master_profile
        if master.status == Master.STATUS_FIRED:
            raise PermissionDenied("Your master profile is not active.")

        return super().dispatch(request, *args, **kwargs)


class TelegramAuthMixin:
    """
    Mixin for views that handle Telegram Web App authentication data.
    """

    def get_telegram_user(self, request):
        """
        Extracts and validates Telegram user data from request.
        This is a placeholder - real implementation needs to validate hash.
        """
        # TODO: Implement real Telegram hash validation
        # For now, we might look for a session variable or GET param (insecure for prod)
        tg_user = request.GET.get("tg_user")
        if tg_user:
            import json

            try:
                return json.loads(tg_user)
            except Exception:  # nosec: B110  # failing to normalize a username as phone is expected/safe
                return None
        return None
