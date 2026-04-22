from __future__ import annotations

from typing import TYPE_CHECKING

from codex_django.cabinet.types import CardGridData, CardItem
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from system.services.loyalty import LoyaltyService

if TYPE_CHECKING:
    from django.db.models import QuerySet


class UserSelector:
    @staticmethod
    def get_users_queryset(segment: str | None = None) -> QuerySet:
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        qs = user_model.objects.select_related("profile").all()

        if segment == "clients":
            qs = qs.filter(profile__source__gt="")
        elif segment == "staff":
            qs = qs.filter(is_staff=True)

        return qs

    @classmethod
    def get_users_grid(cls, segment: str | None = None) -> CardGridData:
        from system.models import Client

        items = []

        # 1. Real Users
        if segment != "shadows":
            queryset = cls.get_users_queryset(segment)
            for user in queryset:
                profile = getattr(user, "profile", None)
                if profile:
                    full_name = profile.get_full_name() or user.get_full_name() or user.username
                    avatar = profile.get_initials()
                    loyalty = LoyaltyService.get_display_for_profile(profile)
                else:
                    full_name = user.get_full_name() or user.username
                    avatar = user.username[0].upper() if user.username else "?"
                    loyalty = None

                items.append(
                    CardItem(
                        id=f"user_{user.pk}",
                        title=f"{full_name}",
                        subtitle=user.email,
                        avatar=avatar,
                        badge=profile.source.capitalize() if profile and profile.source else "",
                        badge_style="primary" if profile and profile.source == "booking" else "secondary",
                        url=str(reverse_lazy("cabinet:user_modal", kwargs={"id_token": f"user_{user.pk}"})),
                        meta=[("bi-stars", loyalty.staff_label)] if loyalty else [],
                    )
                )

        # 2. Ghost Clients (system.Client where user is NULL)
        if segment in ["all", "shadows", "clients"]:
            ghosts = Client.objects.filter(user__isnull=True)

            # Efficiently get user emails/phones from the current grid to avoid duplication
            existing_emails = {i.subtitle.lower() for i in items if i.subtitle and "@" in i.subtitle}

            for ghost in ghosts:
                # Deduplication: if a registered user with same email exists, skip the ghost card
                # The UserService.get_client_detail will "glue" them when the user card is clicked
                if ghost.email and ghost.email.lower() in existing_emails:
                    continue

                items.append(
                    CardItem(
                        id=f"ghost_{ghost.pk}",
                        title=f"{ghost.first_name} {ghost.last_name}".strip() or str(_("Anonymous Client")),
                        subtitle=ghost.email or str(_("No email")),
                        avatar="👻",
                        badge=str(_("Shadow")),
                        badge_style="warning",
                        url=str(reverse_lazy("cabinet:user_modal", kwargs={"id_token": f"ghost_{ghost.pk}"})),
                        meta=[("bi-phone", ghost.phone)] if ghost.phone else [],
                    )
                )

        return CardGridData(
            items=items,
            search_placeholder=str(_("Search users...")),
            empty_message=str(_("No users found")),
        )
