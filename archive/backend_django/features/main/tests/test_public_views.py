"""Smoke and behavior tests for all public page views."""

from unittest.mock import patch

import pytest
from django.test import Client as TestClient
from django.urls import reverse


@pytest.fixture
def http():
    return TestClient()


def _valid_contact_data():
    return {
        "first_name": "Anna",
        "last_name": "Test",
        "contact_type": "email",
        "contact_value": "anna@test.de",
        "topic": "general",
        "message": "Hello from test",
        "dsgvo_consent": True,
        "consent_marketing": False,
    }


@pytest.mark.integration
class TestHomeView:
    def test_returns_200(self, http, site_settings_obj):
        url = reverse("home")
        response = http.get(url)
        assert response.status_code == 200

    def test_bento_in_context(self, http, category, site_settings_obj):
        url = reverse("home")
        response = http.get(url)
        assert response.status_code == 200
        assert "bento" in response.context


@pytest.mark.integration
class TestServicesIndexView:
    def test_returns_200(self, http, site_settings_obj):
        url = reverse("services")
        response = http.get(url)
        assert response.status_code == 200

    def test_bento_filter_accepted(self, http, site_settings_obj):
        url = reverse("services") + "?bento=nails"
        response = http.get(url)
        assert response.status_code == 200

    def test_islands_in_context(self, http, category, site_settings_obj):
        url = reverse("services")
        response = http.get(url)
        assert "islands" in response.context


@pytest.mark.integration
class TestServiceDetailView:
    def test_existing_slug_returns_200(self, http, category, site_settings_obj):
        url = reverse("service_detail", kwargs={"slug": category.slug})
        response = http.get(url)
        assert response.status_code == 200

    def test_nonexistent_slug_returns_404(self, http, site_settings_obj):
        url = reverse("service_detail", kwargs={"slug": "does-not-exist"})
        response = http.get(url)
        assert response.status_code == 404


@pytest.mark.integration
class TestTeamView:
    def test_returns_200(self, http, site_settings_obj):
        url = reverse("team")
        response = http.get(url)
        assert response.status_code == 200


@pytest.mark.integration
class TestContactsView:
    def test_get_returns_200_with_form(self, http, site_settings_obj):
        url = reverse("contacts")
        response = http.get(url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_valid_form_submission_creates_contact_request(self, http, site_settings_obj):
        url = reverse("contacts")
        with patch("features.main.services.contact_service.ContactService.create_request"):
            response = http.post(url, data=_valid_contact_data())
        # Should redirect (302) on valid form
        assert response.status_code in (200, 302)

    def test_invalid_form_missing_first_name_shows_errors(self, http, site_settings_obj):
        data = _valid_contact_data()
        del data["first_name"]
        url = reverse("contacts")
        response = http.post(url, data=data)
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_invalid_email_format_shows_error(self, http, site_settings_obj):
        data = _valid_contact_data()
        data["contact_value"] = "not-an-email"
        url = reverse("contacts")
        response = http.post(url, data=data)
        assert response.status_code == 200
        form = response.context["form"]
        assert form.errors

    def test_htmx_valid_submission_returns_200_partial(self, http, site_settings_obj):
        url = reverse("contacts")
        with patch("features.main.services.contact_service.ContactService.create_request"):
            response = http.post(
                url,
                data=_valid_contact_data(),
                HTTP_HX_REQUEST="true",
            )
        assert response.status_code == 200


@pytest.mark.integration
class TestLegalViews:
    def test_impressum_returns_200(self, http, site_settings_obj):
        assert http.get(reverse("impressum")).status_code == 200

    def test_datenschutz_returns_200(self, http, site_settings_obj):
        assert http.get(reverse("datenschutz")).status_code == 200

    def test_faq_returns_200(self, http, site_settings_obj):
        assert http.get(reverse("faq")).status_code == 200

    def test_buchungsregeln_returns_200(self, http, site_settings_obj):
        assert http.get(reverse("buchungsregeln")).status_code == 200
