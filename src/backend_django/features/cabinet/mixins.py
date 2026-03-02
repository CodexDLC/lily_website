"""Cabinet access mixins for role-based views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class CabinetAccessMixin(LoginRequiredMixin):
    """
    Base mixin for all cabinet views.
    Requires authentication, adds role and client to template context.
    """

    login_url = reverse_lazy("cabinet:login")

    def get_client(self):
        """Return Client linked to current user, or from magic link session."""
        user = self.request.user
        # Check if user has a linked Client record
        client = getattr(user, "client_profile", None)
        if client:
            return client

        # Fallback: search by email if authenticated
        if user.is_authenticated:
            from features.booking.models import Client
            from features.booking.services.client_service import ClientService

            # 1. Try email match
            if user.email:
                client = Client.objects.filter(email=user.email).first()
                if client:
                    return client

            # 2. Try phone match (assuming username might be a phone)
            try:
                normalized_phone = ClientService._normalize_phone(user.username)
                if normalized_phone:
                    client = Client.objects.filter(phone=normalized_phone).first()
                    if client:
                        return client
            except Exception:  # nosec: B110 - failing to normalize a username as phone is expected/safe
                pass

        # Check magic link session
        client_id = self.request.session.get("cabinet_client_id")
        if client_id:
            from features.booking.models import Client

            return Client.objects.filter(pk=client_id).first()
        return None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = self.request.user.is_staff
        ctx["cabinet_client"] = self.get_client()
        return ctx


class AdminRequiredMixin(CabinetAccessMixin):
    """Only staff users can access this view. Clients are redirected to appointments."""

    def dispatch(self, request, *args, **kwargs):
        # 1. First, let LoginRequiredMixin (parent) handle authentication.
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2. If authenticated but not staff, redirect Client to their appointments.
        if not request.user.is_staff:
            return redirect("cabinet:appointments")

        # 3. Otherwise, proceed to the view.
        return super().dispatch(request, *args, **kwargs)


class HtmxCabinetMixin:
    """
    HTMX Router for Cabinet Views.
    Adds `cabinet_base_template` to the context.
    If it's an HTMX request, uses 'cabinet/base_htmx.html' to render only partials.
    If it's a direct browser request, uses 'cabinet/base_cabinet.html'.
    """

    def get_context_data(self, **kwargs):
        # Ensure we call super().get_context_data from ContextMixin
        context_func = getattr(super(), "get_context_data", lambda **kw: kw)
        ctx = context_func(**kwargs)

        request = getattr(self, "request", None)
        is_htmx = False
        if request:
            is_htmx = request.headers.get("HX-Request", False)
            if hasattr(request, "htmx") and request.htmx:
                is_htmx = True

        if is_htmx:
            ctx["cabinet_base_template"] = "cabinet/base_htmx.html"
        else:
            ctx["cabinet_base_template"] = "cabinet/base_cabinet.html"

        return ctx
