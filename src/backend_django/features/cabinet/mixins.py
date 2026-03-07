from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from features.booking.models import Master


class CabinetAccessMixin(LoginRequiredMixin):
    """
    Base mixin for all cabinet views.
    Ensures user is logged in and adds common context.
    """

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = self.request.user.is_staff or self.request.user.is_superuser
        return ctx


class HtmxCabinetMixin:
    """
    Mixin for HTMX views in cabinet.
    Automatically switches base template for HTMX requests to avoid nesting.
    """

    def get_context_data(self, **kwargs):
        # Call super() to get context from other mixins/views
        # We use getattr because HtmxCabinetMixin might be first in MRO
        context_func = getattr(super(), "get_context_data", lambda **kw: kw)
        ctx = context_func(**kwargs)

        # Fix for Mypy: safely get request from self
        request = getattr(self, "request", None)
        is_htmx = False
        if request:
            is_htmx = request.headers.get("HX-Request", False)

        if is_htmx:
            ctx["cabinet_base_template"] = "cabinet/base/base_htmx.html"
        else:
            ctx["cabinet_base_template"] = "cabinet/base_cabinet.html"

        return ctx


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
