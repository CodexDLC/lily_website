from typing import Any, cast

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class CabinetAccountAdapter(DefaultAccountAdapter):  # type: ignore[misc]
    """
    Redirect users after login and route emails through NotificationService (ARQ).
    """

    def get_login_redirect_url(self, request: Any) -> str:
        default_url = cast("str", getattr(settings, "CABINET_DEFAULT_URL", "/cabinet/"))
        client_url = cast("str", getattr(settings, "CABINET_CLIENT_URL", ""))

        if client_url and not (request.user.is_staff or request.user.is_superuser):
            return client_url
        return default_url

    def send_mail(self, template_prefix: str, email: str, context: dict[str, Any]) -> None:
        """
        Intercept allauth emails and route them through our branded NotificationService.
        """
        from features.conversations.services.notifications import NotificationService

        user = context.get("user")
        user_name = "Client"
        if user:
            user_name = getattr(user, "first_name", "") or getattr(user, "username", "Client")

        # Basic language detection (can be expanded)
        lang = getattr(settings, "LANGUAGE_CODE", "de")[:2]

        if template_prefix in [
            "account/email/email_confirmation",
            "account/email/email_confirmation_signup",
        ]:
            signup = template_prefix == "account/email/email_confirmation_signup"
            NotificationService.send_account_verification(
                recipient_email=email,
                activate_url=context.get("activate_url"),
                user_name=user_name,
                signup=signup,
                lang=lang,
            )
        elif template_prefix == "account/email/password_reset_key":
            NotificationService.send_password_reset(
                recipient_email=email,
                reset_url=context.get("password_reset_url"),
                user_name=user_name,
                lang=lang,
            )
        else:
            # For any other emails, we still route to ARQ but maybe with a more generic method
            # For now, fallback to default Allauth (unbranded) for safety on odd templates
            super().send_mail(template_prefix, email, context)
