from __future__ import annotations

from types import SimpleNamespace

from cabinet.adapters import CabinetAccountAdapter
from django.contrib.auth import get_user_model
from system.models import Client, UserProfile


def test_signup_links_shadow_client_and_syncs_profile():
    shadow_client = Client.objects.create(
        first_name="Anna",
        last_name="Client",
        phone="+49111000123",
        email="Anna.Client@Test.Local",
        status=Client.STATUS_GUEST,
        is_ghost=True,
    )
    user_model = get_user_model()
    user = user_model()
    form = SimpleNamespace(
        cleaned_data={
            "email": "anna.client@test.local",
            "password1": "safe-test-password",  # pragma: allowlist secret
        }
    )

    saved_user = CabinetAccountAdapter().save_user(SimpleNamespace(), user, form, commit=True)

    shadow_client.refresh_from_db()
    saved_user.refresh_from_db()
    profile = UserProfile.objects.get(user=saved_user)

    assert shadow_client.user == saved_user
    assert shadow_client.is_ghost is False
    assert shadow_client.status == Client.STATUS_ACTIVE
    assert Client.objects.count() == 1

    assert saved_user.email == "anna.client@test.local"
    assert saved_user.first_name == "Anna"
    assert saved_user.last_name == "Client"

    assert profile.phone == "+49111000123"
    assert profile.first_name == "Anna"
    assert profile.last_name == "Client"
