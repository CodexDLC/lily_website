from typing import Any, cast

from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import reverse_lazy


class AuthModeContextMixin:
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # Mixins for Django views often trigger 'undefined in superclass' in Mypy
        context = super().get_context_data(**kwargs)  # type: ignore[misc]
        context.update(
            {
                "auth_mode": getattr(settings, "CODEX_AUTH_MODE", "django"),
                "auth_provider": getattr(settings, "CODEX_AUTH_PROVIDER", "django"),
                "allauth_enabled": bool(getattr(settings, "CODEX_ALLAUTH_ENABLED", False)),
            }
        )
        return cast("dict[str, Any]", context)


class BrandedLoginView(AuthModeContextMixin, LoginView):
    template_name = "account/login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True


class BrandedLogoutView(AuthModeContextMixin, LogoutView):
    template_name = "account/logout.html"


class BrandedPasswordResetView(AuthModeContextMixin, PasswordResetView):
    template_name = "account/password_reset.html"
    email_template_name = "registration/password_reset_email.html"
    form_class = PasswordResetForm
    success_url = reverse_lazy("cabinet:account_reset_password_done")


class BrandedPasswordResetDoneView(AuthModeContextMixin, PasswordResetDoneView):
    template_name = "account/password_reset_done.html"


class BrandedPasswordResetConfirmView(AuthModeContextMixin, PasswordResetConfirmView):
    template_name = "account/password_reset.html"
    success_url = reverse_lazy("password_reset_complete")


class BrandedPasswordResetCompleteView(AuthModeContextMixin, PasswordResetCompleteView):
    template_name = "account/password_reset_done.html"
