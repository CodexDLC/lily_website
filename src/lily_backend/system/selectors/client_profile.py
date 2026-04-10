from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

from system.models import UserProfile

User = get_user_model()


class ClientProfileSelector:
    @staticmethod
    def get_or_create_profile(user: AbstractBaseUser | Any) -> UserProfile:
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "first_name": getattr(user, "first_name", ""),
                "last_name": getattr(user, "last_name", ""),
                "source": "manual",
            },
        )
        return profile
