"""Client profile view."""

from core.logger import log
from django.views.generic import TemplateView
from features.cabinet.mixins import CabinetAccessMixin, HtmxCabinetMixin


class ProfileView(HtmxCabinetMixin, CabinetAccessMixin, TemplateView):
    template_name = "cabinet/profile/index.html"

    def get_context_data(self, **kwargs):
        log.debug(f"View: ProfileView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "profile"
        client = ctx.get("cabinet_client")

        if not client and not self.request.user.is_staff:
            log.warning(
                f"View: ProfileView | Action: AccessDenied | user={self.request.user.id} | reason=NoClientFound"
            )
            return ctx

        ctx["profile_client"] = client
        log.info(
            f"View: ProfileView | Action: Success | user={self.request.user.id} | client_id={client.id if client else 'Staff'}"
        )
        return ctx
