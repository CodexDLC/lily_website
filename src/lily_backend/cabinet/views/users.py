from __future__ import annotations

from typing import Any

from django.views.generic import TemplateView

from cabinet.mixins import StaffRequiredMixin
from cabinet.services.users import UserService


class UserListView(StaffRequiredMixin, TemplateView):
    """
    Modular user list view for the cabinet dashboard.

    Supports 'segment' query parameter for smart filtering.
    Sets 'cabinet_module' on the request for topbar/sidebar active state.
    """

    template_name = "cabinet/users/list.html"
    module_name: str = "users"  # Default name, can be overridden by config

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        # Allow dynamic naming of the module from the request if needed
        # (e.g. from the cabinet registry context)
        request.cabinet_module = getattr(self, "module_name", "users")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(UserService.get_list_context(self.request))
        return context


class ClientDetailView(StaffRequiredMixin, TemplateView):
    """
    Modal content for client/user detail editing.
    """

    template_name = "cabinet/users/includes/modal_client_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        id_token = self.kwargs.get("id_token", "")
        context.update(UserService.get_client_detail(id_token))
        return context
