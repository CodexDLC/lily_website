"""Tests for MastersView HTMX CRUD."""

import pytest
from django.test import Client as TestClient
from django.urls import reverse
from features.booking.models.master import Master


@pytest.fixture
def http():
    return TestClient()


@pytest.mark.integration
class TestMastersView:
    def test_anonymous_redirected(self, http):
        url = reverse("cabinet:masters")
        response = http.get(url)
        assert response.status_code in (302, 403)

    def test_non_staff_denied(self, http, master_user):
        http.force_login(master_user)
        url = reverse("cabinet:masters")
        response = http.get(url)
        assert response.status_code in (302, 403)

    def test_admin_sees_masters_list(self, http, admin_user, master):
        http.force_login(admin_user)
        url = reverse("cabinet:masters")
        response = http.get(url)
        assert response.status_code == 200
        assert "masters" in response.context

    def test_master_appears_in_list(self, http, admin_user, master):
        http.force_login(admin_user)
        url = reverse("cabinet:masters")
        response = http.get(url)
        assert master in response.context["masters"]

    def test_edit_action_returns_200(self, http, admin_user, master):
        http.force_login(admin_user)
        url = reverse("cabinet:masters") + f"?action=edit&id={master.id}"
        response = http.get(url)
        assert response.status_code == 200

    def test_view_action_returns_200(self, http, admin_user, master):
        http.force_login(admin_user)
        url = reverse("cabinet:masters") + f"?action=view&id={master.id}"
        response = http.get(url)
        assert response.status_code == 200

    def test_save_action_updates_master_name(self, http, admin_user, master):
        http.force_login(admin_user)
        url = reverse("cabinet:masters") + f"?action=save&id={master.id}"
        response = http.post(
            url,
            data={
                "action": "save",
                "id": master.id,
                "name": "Updated Name",
                "status": Master.STATUS_ACTIVE,
                "is_public": "on",
            },
        )
        assert response.status_code == 200
        master.refresh_from_db()
        assert master.name == "Updated Name"

    def test_show_fired_includes_fired_masters(self, http, admin_user, category):
        http.force_login(admin_user)
        fired = Master.objects.create(
            name="Fired Master",
            slug="fired-master",
            status=Master.STATUS_FIRED,
            work_days=[],
        )
        url = reverse("cabinet:masters") + "?show_fired=1"
        response = http.get(url)
        assert fired in response.context["masters"]

    def test_status_filter_active_only(self, http, admin_user, master, category):
        http.force_login(admin_user)
        fired = Master.objects.create(
            name="Fired2",
            slug="fired-master-2",
            status=Master.STATUS_FIRED,
            work_days=[],
        )
        url = reverse("cabinet:masters") + "?status=active"
        response = http.get(url)
        masters = response.context["masters"]
        assert master in masters
        assert fired not in masters
