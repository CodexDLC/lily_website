"""Tests for ClientsView HTMX CRUD."""

import pytest
from django.test import Client as TestClient
from django.urls import reverse
from features.booking.models.client import Client


@pytest.fixture
def http():
    return TestClient()


@pytest.mark.integration
class TestClientsView:
    def test_anonymous_redirected(self, http):
        url = reverse("cabinet:clients")
        response = http.get(url)
        assert response.status_code in (302, 403)

    def test_non_staff_denied(self, http, master_user):
        http.force_login(master_user)
        url = reverse("cabinet:clients")
        response = http.get(url)
        assert response.status_code in (302, 403)

    def test_admin_sees_clients_list(self, http, admin_user, client_obj):
        http.force_login(admin_user)
        url = reverse("cabinet:clients")
        response = http.get(url)
        assert response.status_code == 200
        assert "page_obj" in response.context

    def test_search_by_first_name(self, http, admin_user):
        http.force_login(admin_user)
        Client.objects.create(first_name="Unique", last_name="Name", phone="+49111222333")
        Client.objects.create(first_name="Other", last_name="Person", phone="+49111222444")
        url = reverse("cabinet:clients") + "?q=Unique"
        response = http.get(url)
        page = response.context["page_obj"]
        names = [c.first_name for c in page.object_list]
        assert "Unique" in names
        assert "Other" not in names

    def test_search_by_phone(self, http, admin_user):
        http.force_login(admin_user)
        c = Client.objects.create(phone="+49999888777", first_name="Phone")
        url = reverse("cabinet:clients") + "?q=+49999888777"
        response = http.get(url)
        page = response.context["page_obj"]
        assert c in page.object_list

    def test_edit_action_returns_200(self, http, admin_user, client_obj):
        http.force_login(admin_user)
        url = reverse("cabinet:clients") + f"?action=edit&id={client_obj.id}"
        response = http.get(url)
        assert response.status_code == 200

    def test_view_action_returns_200(self, http, admin_user, client_obj):
        http.force_login(admin_user)
        url = reverse("cabinet:clients") + f"?action=view&id={client_obj.id}"
        response = http.get(url)
        assert response.status_code == 200

    def test_save_action_updates_client(self, http, admin_user, client_obj):
        http.force_login(admin_user)
        url = reverse("cabinet:clients") + f"?action=save&id={client_obj.id}"
        response = http.post(
            url,
            data={
                "action": "save",
                "id": client_obj.id,
                "first_name": "Updated",
                "last_name": "Client",
                "phone": client_obj.phone,
                "email": client_obj.email,
            },
        )
        assert response.status_code == 200
        client_obj.refresh_from_db()
        assert client_obj.first_name == "Updated"

    def test_search_returns_empty_when_no_match(self, http, admin_user, client_obj):
        http.force_login(admin_user)
        url = reverse("cabinet:clients") + "?q=ZZZnonexistent"
        response = http.get(url)
        assert response.context["page_obj"].paginator.count == 0
