from typing import Any, cast

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.utils.translation import get_language


class CabinetAccountAdapter(DefaultAccountAdapter):  # type: ignore[misc]
    """
    Redirect users after login and route emails through NotificationService (ARQ).
    """

    def get_login_redirect_url(self, request: Any) -> str:
        user = request.user
        # Strict staff check: must have is_staff or be in Staff group
        is_staff_member = user.is_staff or user.is_superuser or user.groups.filter(name="Staff").exists()

        if is_staff_member:
            return cast("str", getattr(settings, "CABINET_DEFAULT_URL", "/cabinet/"))

        # Regular clients always go to client cabinet
        return cast("str", getattr(settings, "CABINET_CLIENT_URL", "/cabinet/my/"))

    def save_user(self, request: Any, user: Any, form: Any, commit: bool = True) -> Any:
        """
        Link newly registered user to an existing ghost client and sync data.
        """
        user = super().save_user(request, user, form, commit=commit)
        if commit:
            from system.models import Client, UserProfile

            # Try to find a ghost client with the same email.
            client = None
            if user.email:
                client = Client.objects.filter(email__iexact=user.email, user__isnull=True).first()
            if client:
                client.user = user
                client.is_ghost = False
                client.status = Client.STATUS_ACTIVE
                client.save(update_fields=["user", "is_ghost", "status", "updated_at"])

                # Sync base user data if empty
                user_updated = False
                if not user.first_name and client.first_name:
                    user.first_name = client.first_name
                    user_updated = True
                if not user.last_name and client.last_name:
                    user.last_name = client.last_name
                    user_updated = True
                if user_updated:
                    user.save(update_fields=["first_name", "last_name"])

                # Sync core UserProfile data
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile_updated = False
                if not profile.phone and client.phone:
                    profile.phone = client.phone
                    profile_updated = True
                if not profile.first_name and client.first_name:
                    profile.first_name = client.first_name
                    profile_updated = True
                if not profile.last_name and client.last_name:
                    profile.last_name = client.last_name
                    profile_updated = True
                if profile_updated:
                    profile.save(update_fields=["phone", "first_name", "last_name", "updated_at"])
        return user

    def send_mail(self, template_prefix: str, email: str, context: dict[str, Any]) -> None:
        """
        Intercept allauth emails and route them through our branded NotificationService.
        """
        from features.conversations.services.notifications import NotificationService

        user = context.get("user")
        user_name = "Client"
        if user:
            user_name = getattr(user, "first_name", "") or getattr(user, "username", "Client")

        request = context.get("request")
        lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or getattr(settings, "LANGUAGE_CODE", "en"))[
            :2
        ]

        def _fix_url(url: str | None) -> str | None:
            if not url:
                return url
            base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
            if not base:
                return url
            from urllib.parse import urlparse

            parsed = urlparse(url)
            # Replace scheme and netloc with those from settings.SITE_BASE_URL
            parsed_base = urlparse(base)
            new_url = parsed._replace(scheme=parsed_base.scheme, netloc=parsed_base.netloc)
            return new_url.geturl()

        if template_prefix in [
            "account/email/email_confirmation",
            "account/email/email_confirmation_signup",
        ]:
            signup = template_prefix == "account/email/email_confirmation_signup"
            NotificationService.send_account_verification(
                recipient_email=email,
                activate_url=_fix_url(context.get("activate_url")),
                user_name=user_name,
                signup=signup,
                lang=lang,
            )
        elif template_prefix == "account/email/password_reset_key":
            NotificationService.send_password_reset(
                recipient_email=email,
                reset_url=_fix_url(context.get("password_reset_url")),
                user_name=user_name,
                lang=lang,
            )
        elif template_prefix == "account/email/account_already_exists":
            NotificationService.send_account_already_exists(
                recipient_email=email,
                password_reset_url=_fix_url(context.get("password_reset_url")),
                lang=lang,
            )
        else:
            # For any other emails, we still route to ARQ but maybe with a more generic method
            # For now, fallback to default Allauth (unbranded) for safety on odd templates
            super().send_mail(template_prefix, email, context)
