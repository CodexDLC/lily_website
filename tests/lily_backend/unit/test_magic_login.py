import pytest
from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner
from django.urls import reverse


@pytest.mark.django_db
def test_magic_login_success(client):
    user_model = get_user_model()
    user_model.objects.create_user(username="staff", email="staff@example.com", is_staff=True)

    signer = TimestampSigner()
    token = signer.sign("staff@example.com")

    url = reverse("cabinet:magic_login") + f"?token={token}"
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("cabinet:site_settings")


@pytest.mark.django_db
def test_magic_login_fallback_to_superuser(client):
    user_model = get_user_model()
    user_model.objects.create_superuser(username="admin", email="admin@example.com", password="password")  # pragma: allowlist secret

    signer = TimestampSigner()
    token = signer.sign("some-alias@example.com")

    url = reverse("cabinet:magic_login") + f"?token={token}"
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("cabinet:site_settings")


@pytest.mark.django_db
def test_magic_login_invalid_token(client):
    url = reverse("cabinet:magic_login") + "?token=invalid"
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse("account_login")


@pytest.mark.django_db
def test_magic_login_expired_token(client):
    signer = TimestampSigner()
    token = signer.sign("staff@example.com")
    # We can't easily travel in time here without freezegun, but we can tamper with the token
    tampered_token = token + "expired"
    url = reverse("cabinet:magic_login") + f"?token={tampered_token}"
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse("account_login")
