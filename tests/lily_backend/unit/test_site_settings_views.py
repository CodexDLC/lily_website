from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.urls import reverse

from src.lily_backend.cabinet.views.site_settings import site_settings_tab_view, site_settings_view


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def owner_user():
    user = MagicMock()
    user.is_active = True
    user.is_superuser = True
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_service():
    with patch("src.lily_backend.cabinet.views.site_settings.SiteSettingsService") as mock:
        yield mock


def test_site_settings_view_get(rf, owner_user, mock_service):
    url = reverse("cabinet:site_settings")
    request = rf.get(url)
    request.user = owner_user

    mock_service.get_context.return_value = {"settings": {}}

    # Needs messages framework mock
    with patch("django.contrib.messages.success"), patch("django.contrib.messages.error"):
        response = site_settings_view(request)

    assert response.status_code == 200
    mock_service.get_context.assert_called_once()


def test_site_settings_view_post_success(rf, owner_user, mock_service):
    url = reverse("cabinet:site_settings")
    request = rf.post(url, data={"company_name": "Lily"})
    request.user = owner_user

    mock_service.save_context.return_value = (True, "Saved")
    mock_service.get_context.return_value = {}

    with patch("django.contrib.messages.success") as mock_success:
        response = site_settings_view(request)
        mock_success.assert_called_with(request, "Saved")

    assert response.status_code == 200


def test_site_settings_view_post_error(rf, owner_user, mock_service):
    url = reverse("cabinet:site_settings")
    request = rf.post(url, data={})
    request.user = owner_user

    mock_service.save_context.return_value = (False, "Error")
    mock_service.get_context.return_value = {}

    with patch("django.contrib.messages.error") as mock_error:
        response = site_settings_view(request)
        mock_error.assert_called_with(request, "Error")

    assert response.status_code == 200


def test_site_settings_tab_view(rf, owner_user):
    url = reverse("cabinet:site_settings_tab", kwargs={"tab_slug": "email"})
    request = rf.get(url)
    request.user = owner_user

    response = site_settings_tab_view(request, tab_slug="email")

    assert response.status_code == 302
    assert "#email" in response.url
