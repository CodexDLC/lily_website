"""Tests for PromoService and PromoMessage model."""

from datetime import timedelta

import pytest
from django.utils import timezone
from features.promos.models import PromoMessage
from features.promos.services.notification_service import PromoService


def _make_promo(title="Test Promo", priority=0, target_pages="", is_active=True, offset_hours=1):
    """Helper: creates an active PromoMessage."""
    return PromoMessage.objects.create(
        title=title,
        description="Test description",
        is_active=is_active,
        starts_at=timezone.now() - timedelta(hours=offset_hours),
        ends_at=timezone.now() + timedelta(hours=offset_hours),
        target_pages=target_pages,
        priority=priority,
    )


@pytest.mark.integration
class TestPromoServiceGetActivePromo:
    def test_returns_active_promo_for_any_page(self):
        promo = _make_promo()
        result = PromoService.get_active_promo(page_slug="home")
        assert result is not None
        assert result.pk == promo.pk

    def test_returns_highest_priority_promo(self):
        _make_promo(title="Low Priority", priority=0)
        high = _make_promo(title="High Priority", priority=10)
        result = PromoService.get_active_promo()
        assert result.pk == high.pk

    def test_returns_specific_page_promo(self):
        promo = _make_promo(target_pages="home")
        result = PromoService.get_active_promo(page_slug="home")
        assert result is not None
        assert result.pk == promo.pk

    def test_does_not_return_promo_for_wrong_page(self):
        _make_promo(target_pages="home")
        result = PromoService.get_active_promo(page_slug="services")
        # Only has "home" promo — but target_pages="home" won't match "services"
        # However a promo with target_pages="" would match — none created here
        assert result is None

    def test_inactive_promo_not_returned(self):
        _make_promo(is_active=False)
        result = PromoService.get_active_promo(page_slug="home")
        assert result is None

    def test_expired_promo_not_returned(self):
        PromoMessage.objects.create(
            title="Expired",
            description="desc",
            is_active=True,
            starts_at=timezone.now() - timedelta(hours=2),
            ends_at=timezone.now() - timedelta(hours=1),
        )
        result = PromoService.get_active_promo(page_slug="home")
        assert result is None

    def test_scheduled_promo_not_returned(self):
        PromoMessage.objects.create(
            title="Future",
            description="desc",
            is_active=True,
            starts_at=timezone.now() + timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=2),
        )
        result = PromoService.get_active_promo(page_slug="home")
        assert result is None

    def test_returns_none_when_no_promos(self):
        result = PromoService.get_active_promo()
        assert result is None


@pytest.mark.integration
class TestPromoServiceTracking:
    def test_track_view_increments_counter(self):
        promo = _make_promo()
        assert promo.views_count == 0
        PromoService.track_view(promo.pk)
        promo.refresh_from_db()
        assert promo.views_count == 1

    def test_track_view_increments_multiple_times(self):
        promo = _make_promo()
        PromoService.track_view(promo.pk)
        PromoService.track_view(promo.pk)
        promo.refresh_from_db()
        assert promo.views_count == 2

    def test_track_click_increments_counter(self):
        promo = _make_promo()
        PromoService.track_click(promo.pk)
        promo.refresh_from_db()
        assert promo.clicks_count == 1

    def test_is_promo_active_true(self):
        promo = _make_promo()
        assert PromoService.is_promo_active(promo.pk) is True

    def test_is_promo_active_false_when_expired(self):
        promo = PromoMessage.objects.create(
            title="Expired",
            description="desc",
            is_active=True,
            starts_at=timezone.now() - timedelta(hours=2),
            ends_at=timezone.now() - timedelta(hours=1),
        )
        assert PromoService.is_promo_active(promo.pk) is False

    def test_is_promo_active_false_when_inactive_flag(self):
        promo = _make_promo(is_active=False)
        assert PromoService.is_promo_active(promo.pk) is False

    def test_is_promo_active_false_for_nonexistent(self):
        assert PromoService.is_promo_active(99999) is False


@pytest.mark.integration
class TestGetAllActivePromos:
    def test_returns_multiple_promos(self):
        _make_promo(title="P1", priority=0)
        _make_promo(title="P2", priority=5)
        result = PromoService.get_all_active_promos()
        assert result.count() == 2

    def test_ordered_by_priority_desc(self):
        _make_promo(title="Low", priority=0)
        _make_promo(title="High", priority=10)
        result = list(PromoService.get_all_active_promos())
        assert result[0].title == "High"
        assert result[1].title == "Low"
