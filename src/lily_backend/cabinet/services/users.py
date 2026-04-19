from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from django.utils.translation import gettext_lazy as _
from system.selectors.client_profile import ClientProfileSelector
from system.selectors.users import UserSelector
from system.services.loyalty import LoyaltyService

if TYPE_CHECKING:
    from django.http import HttpRequest


class UserService:
    """Page-service contract for cabinet users pages.

    Returns:
        cards: CardGridData for ``cabinet/components/card_grid.html``
        header_title: page heading
        header_subtitle: segment-specific page title
        active_segment: current querystring segment

    Data source:
        ``system.selectors.users.UserSelector``
    """

    _SEGMENT_TITLES: ClassVar[dict[str, str]] = {
        "all": str(_("All Users")),
        "clients": str(_("Clients")),
        "shadows": str(_("Shadow Users")),
        "staff": str(_("Staff")),
    }

    @classmethod
    def get_list_context(cls, request: HttpRequest) -> dict[str, object]:
        segment = request.GET.get("segment", "all")
        return {
            "cards": UserSelector.get_users_grid(segment=segment),
            "header_title": str(_("Administration")),
            "header_subtitle": cls._SEGMENT_TITLES.get(segment, str(_("Users"))),
            "active_segment": segment,
        }

    @classmethod
    def get_client_detail(cls, id_token: str) -> dict[str, object]:
        """
        Fetch detail data for a single client or user.
        id_token can be 'user_INT' or 'ghost_INT'.
        """
        from django.contrib.auth import get_user_model
        from system.models import Client

        user_model = get_user_model()
        client = None

        if id_token.startswith("ghost_"):
            try:
                pk = int(id_token.replace("ghost_", ""))
                client = Client.objects.filter(pk=pk).select_related("user", "user__profile").first()
            except (ValueError, Client.DoesNotExist):
                pass
        elif id_token.startswith("user_"):
            try:
                pk = int(id_token.replace("user_", ""))
                user = user_model.objects.filter(pk=pk).select_related("profile").first()
                if user:
                    # 1. Try to find associated client record by FK
                    client = Client.objects.filter(user=user).first()
                    # 2. If no FK, try "gluing" by email or phone
                    if not client:
                        # Find orphaned client by email
                        if user.email:
                            client = Client.objects.filter(email__iexact=user.email, user__isnull=True).first()
                        # Or by phone from profile
                        if not client and hasattr(user, "profile") and user.profile.phone:
                            client = Client.objects.filter(phone=user.profile.phone, user__isnull=True).first()
                        if client:
                            # Perform the "Gluing" (Link the orphan to the registered user)
                            client.user = user
                            client.is_ghost = False
                            client.save()
                    # 3. If still no client, create and SAVE a new one for the modal view
                    if not client:
                        client = Client.objects.create(
                            first_name=user.first_name,
                            last_name=user.last_name,
                            email=user.email,
                            user=user,
                            is_ghost=False,
                        )
            except (ValueError, user_model.DoesNotExist):
                pass

        user = getattr(client, "user", None)
        profile = getattr(user, "profile", None)
        if profile is None and user is not None:
            profile = ClientProfileSelector.get_or_create_profile(user)
        return {
            "client": client,
            "loyalty": LoyaltyService.get_display_for_profile(profile),
        }
