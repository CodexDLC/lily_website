"""Shared auth/permission mixins for cabinet views."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow only users with is_staff=True or is_superuser=True.

    Redirects unauthenticated users to login page (LoginRequiredMixin).
    Returns 403 for authenticated non-staff users (UserPassesTestMixin).
    """

    raise_exception = True  # return 403 instead of redirect for logged-in non-staff

    def test_func(self) -> bool:
        user = self.request.user  # type: ignore[attr-defined]
        return bool(user.is_active and (user.is_staff or user.is_superuser))


class OwnerRequiredMixin(StaffRequiredMixin):
    """Allow only users with is_superuser=True (salon owner / admin)."""

    def test_func(self) -> bool:
        user = self.request.user  # type: ignore[attr-defined]
        return bool(user.is_active and user.is_superuser)
