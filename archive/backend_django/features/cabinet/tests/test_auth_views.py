"""Tests for cabinet auth views: login, logout, magic link."""

import pytest
from django.test import Client as TestClient
from django.urls import reverse

_TEST_PASSWORD = "testpass123"  # nosec B105  # pragma: allowlist secret


@pytest.fixture
def http():
    return TestClient()


@pytest.mark.integration
class TestCabinetLoginView:
    def test_get_login_page_returns_200(self, http):
        url = reverse("cabinet:login")
        response = http.get(url)
        assert response.status_code == 200

    def test_authenticated_admin_redirected_from_login(self, http, admin_user):
        http.force_login(admin_user)
        url = reverse("cabinet:login")
        response = http.get(url)
        assert response.status_code == 302
        assert "dashboard" in response.url

    def test_authenticated_staff_user_redirected_to_appointments(self, http, master_user):
        http.force_login(master_user)
        url = reverse("cabinet:login")
        response = http.get(url)
        assert response.status_code == 302

    def test_valid_login_staff_redirects_to_dashboard(self, http, admin_user):
        url = reverse("cabinet:login")
        response = http.post(url, data={"username": "admin_root", "password": _TEST_PASSWORD})
        assert response.status_code == 302
        assert "dashboard" in response.url

    def test_valid_login_non_staff_redirects_to_appointments(self, http, master_user):
        url = reverse("cabinet:login")
        response = http.post(url, data={"username": "master_user", "password": _TEST_PASSWORD})
        assert response.status_code == 302
        assert "appointments" in response.url

    def test_invalid_login_shows_error(self, http, admin_user):
        url = reverse("cabinet:login")
        response = http.post(url, data={"username": "admin_root", "password": "wrongpassword"})
        assert response.status_code == 200
        assert b"\xd0\x9d\xd0\xb5\xd0\xb2\xd0\xb5\xd1\x80\xd0\xbd" in response.content  # "Неверн"


@pytest.mark.integration
class TestCabinetLogoutView:
    def test_logout_clears_session_and_redirects(self, http, admin_user):
        http.force_login(admin_user)
        url = reverse("cabinet:logout")
        response = http.post(url)
        assert response.status_code == 302

    def test_get_logout_redirects(self, http, admin_user):
        http.force_login(admin_user)
        url = reverse("cabinet:logout")
        response = http.get(url)
        assert response.status_code == 302

    def test_logout_unauthenticates_user(self, http, admin_user):
        http.force_login(admin_user)
        http.post(reverse("cabinet:logout"))
        # After logout, accessing admin-only page should redirect
        response = http.get(reverse("cabinet:dashboard"))
        assert response.status_code in (302, 403)


@pytest.mark.integration
class TestMagicLinkView:
    def test_valid_token_guest_stored_in_session(self, http, client_obj):
        url = reverse("cabinet:magic_link", kwargs={"token": client_obj.access_token})
        response = http.get(url)
        assert response.status_code == 302
        assert "appointments" in response.url
        # Session should have cabinet_client_id
        assert http.session.get("cabinet_client_id") == client_obj.pk

    def test_valid_token_with_linked_user_logs_in(self, http, client_obj, admin_user):

        client_obj.user = admin_user
        client_obj.status = "active"
        client_obj.save()
        url = reverse("cabinet:magic_link", kwargs={"token": client_obj.access_token})
        response = http.get(url)
        assert response.status_code == 302

    def test_invalid_token_shows_error(self, http):
        url = reverse("cabinet:magic_link", kwargs={"token": "invalid-token-xyz"})
        response = http.get(url)
        assert response.status_code == 200
        assert b"\xd0\xbd\xd0\xb5\xd0\xb4\xd0\xb5\xd0\xb9\xd1\x81" in response.content  # "недейс"
