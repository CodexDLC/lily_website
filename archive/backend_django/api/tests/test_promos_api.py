"""
Integration tests for api/promos.py endpoints.
Tests GET /api/v1/promos/active/ and POST /api/v1/promos/{id}/track-view/ etc.
"""

from datetime import timedelta

import pytest
from django.test import Client as TestClient
from django.utils import timezone
from features.promos.models import PromoMessage


def _make_promo(
    title="Test Promo",
    is_active=True,
    starts_offset_hours=-1,
    ends_offset_hours=1,
    priority=0,
    target_pages="",
):
    """Helper: create a PromoMessage."""
    now = timezone.now()
    return PromoMessage.objects.create(
        title=title,
        description="Test description for promo",
        is_active=is_active,
        starts_at=now + timedelta(hours=starts_offset_hours),
        ends_at=now + timedelta(hours=ends_offset_hours),
        priority=priority,
        target_pages=target_pages,
    )


@pytest.fixture
def http():
    return TestClient()


@pytest.mark.django_db
class TestGetActivePromoEndpoint:
    BASE_URL = "/api/v1/promos/active/"

    def test_returns_200_with_active_promo(self, http):
        _make_promo()
        response = http.get(self.BASE_URL)
        assert response.status_code == 200

    def test_returns_404_when_no_active_promo(self, http):
        response = http.get(self.BASE_URL)
        assert response.status_code == 404

    def test_returns_404_for_inactive_promo(self, http):
        _make_promo(is_active=False)
        response = http.get(self.BASE_URL)
        assert response.status_code == 404

    def test_returns_404_for_expired_promo(self, http):
        _make_promo(starts_offset_hours=-2, ends_offset_hours=-1)
        response = http.get(self.BASE_URL)
        assert response.status_code == 404

    def test_returns_404_for_scheduled_promo(self, http):
        _make_promo(starts_offset_hours=1, ends_offset_hours=2)
        response = http.get(self.BASE_URL)
        assert response.status_code == 404

    def test_response_contains_expected_fields(self, http):
        _make_promo(title="Summer Sale")
        response = http.get(self.BASE_URL)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "description" in data
        assert "button_text" in data
        assert "button_color" in data
        assert "text_color" in data
        assert "display_delay" in data

    def test_response_id_matches_promo(self, http):
        promo = _make_promo()
        response = http.get(self.BASE_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == promo.pk

    def test_response_title_matches_promo(self, http):
        _make_promo(title="My Test Promo Title")
        response = http.get(self.BASE_URL)
        data = response.json()
        assert data["title"] == "My Test Promo Title"

    def test_with_page_slug_parameter(self, http):
        _make_promo(target_pages="home")
        response = http.get(self.BASE_URL + "?page=home")
        assert response.status_code == 200

    def test_with_wrong_page_slug_returns_404(self, http):
        _make_promo(target_pages="home")
        # "services" page — only "home" promo, so no match
        response = http.get(self.BASE_URL + "?page=services")
        assert response.status_code == 404

    def test_returns_highest_priority_promo(self, http):
        _make_promo(title="Low Priority", priority=0)
        high = _make_promo(title="High Priority", priority=10)
        response = http.get(self.BASE_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == high.pk

    def test_image_url_is_none_without_image(self, http):
        _make_promo()
        response = http.get(self.BASE_URL)
        data = response.json()
        assert data["image_url"] is None


@pytest.mark.django_db
class TestTrackViewEndpoint:
    def _url(self, promo_id):
        return f"/api/v1/promos/{promo_id}/track-view/"

    def test_track_view_returns_200(self, http):
        promo = _make_promo()
        response = http.post(self._url(promo.pk))
        assert response.status_code == 200

    def test_track_view_increments_count(self, http):
        promo = _make_promo()
        assert promo.views_count == 0
        http.post(self._url(promo.pk))
        promo.refresh_from_db()
        assert promo.views_count == 1

    def test_track_view_returns_success_true(self, http):
        promo = _make_promo()
        response = http.post(self._url(promo.pk))
        data = response.json()
        assert data["success"] is True

    def test_track_view_response_has_message(self, http):
        promo = _make_promo()
        response = http.post(self._url(promo.pk))
        data = response.json()
        assert "message" in data

    def test_track_view_404_for_inactive_promo(self, http):
        promo = _make_promo(is_active=False)
        response = http.post(self._url(promo.pk))
        assert response.status_code == 404

    def test_track_view_404_for_expired_promo(self, http):
        promo = _make_promo(starts_offset_hours=-2, ends_offset_hours=-1)
        response = http.post(self._url(promo.pk))
        assert response.status_code == 404

    def test_track_view_404_for_nonexistent_promo(self, http):
        response = http.post(self._url(99999))
        assert response.status_code == 404

    def test_track_view_multiple_increments(self, http):
        promo = _make_promo()
        http.post(self._url(promo.pk))
        http.post(self._url(promo.pk))
        http.post(self._url(promo.pk))
        promo.refresh_from_db()
        assert promo.views_count == 3


@pytest.mark.django_db
class TestTrackClickEndpoint:
    def _url(self, promo_id):
        return f"/api/v1/promos/{promo_id}/track-click/"

    def test_track_click_returns_200(self, http):
        promo = _make_promo()
        response = http.post(self._url(promo.pk))
        assert response.status_code == 200

    def test_track_click_increments_count(self, http):
        promo = _make_promo()
        assert promo.clicks_count == 0
        http.post(self._url(promo.pk))
        promo.refresh_from_db()
        assert promo.clicks_count == 1

    def test_track_click_returns_success_true(self, http):
        promo = _make_promo()
        response = http.post(self._url(promo.pk))
        data = response.json()
        assert data["success"] is True

    def test_track_click_404_for_inactive_promo(self, http):
        promo = _make_promo(is_active=False)
        response = http.post(self._url(promo.pk))
        assert response.status_code == 404

    def test_track_click_404_for_nonexistent(self, http):
        response = http.post(self._url(99999))
        assert response.status_code == 404

    def test_track_click_independent_from_views(self, http):
        promo = _make_promo()
        self._url_view = f"/api/v1/promos/{promo.pk}/track-view/"
        http.post(self._url_view)  # track view
        http.post(self._url(promo.pk))  # track click
        promo.refresh_from_db()
        assert promo.views_count == 1
        assert promo.clicks_count == 1
