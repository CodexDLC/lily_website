"""Client profile view."""

from django.views.generic import TemplateView
from features.cabinet.mixins import CabinetAccessMixin, HtmxCabinetMixin


class ProfileView(HtmxCabinetMixin, CabinetAccessMixin, TemplateView):
    template_name = "cabinet/profile/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "profile"
        client = ctx.get("cabinet_client")
        if not client and not self.request.user.is_staff:
            return ctx
        ctx["profile_client"] = client
        return ctx
