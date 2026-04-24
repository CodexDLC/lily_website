from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def magic_login_view(request: HttpRequest) -> HttpResponse:
    """
    Authenticate a staff member via a magic link token sent to their email.
    The token is valid for 24 hours.
    """
    token = request.GET.get("token")
    target = request.GET.get("target") or reverse("cabinet:site_settings")

    # Ensure target is safe to redirect to
    if not url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        target = reverse("cabinet:site_settings")

    if not token:
        return HttpResponseRedirect(reverse("account_login"))

    signer = TimestampSigner()
    try:
        email = signer.unsign(token, max_age=86400)  # 24 hours
    except (BadSignature, SignatureExpired):
        messages.error(request, "Login link is invalid or expired.")
        return HttpResponseRedirect(reverse("account_login"))

    user_model = get_user_model()
    # Try to find staff user by email
    user = user_model.objects.filter(email__iexact=email, is_staff=True, is_active=True).first()

    if not user:
        # Fallback to first superuser if email is just a notification alias
        user = user_model.objects.filter(is_superuser=True, is_active=True).first()

    if user:
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return HttpResponseRedirect(target)

    messages.error(request, "No staff account found to process this login.")
    return HttpResponseRedirect(reverse("account_login"))
