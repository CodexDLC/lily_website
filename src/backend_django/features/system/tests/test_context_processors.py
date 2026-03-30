"""Tests for all context processors."""

from unittest.mock import patch

import pytest
from django.test import RequestFactory
from features.system.context_processors import site_settings, static_content


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.unit
class TestSeoSettingsContextProcessor:
    def test_returns_canonical_domain(self, rf):
        from core.context_processors import seo_settings

        request = rf.get("/")
        result = seo_settings(request)
        assert "CANONICAL_DOMAIN" in result
        assert result["CANONICAL_DOMAIN"].startswith("https://")

    def test_canonical_domain_has_value(self, rf):
        from core.context_processors import seo_settings

        request = rf.get("/")
        result = seo_settings(request)
        assert len(result["CANONICAL_DOMAIN"]) > 0


@pytest.mark.unit
class TestSiteSettingsContextProcessor:
    def test_returns_site_settings_dict(self, rf):
        request = rf.get("/")
        # mock_site_settings_redis autouse fixture already patches load_from_redis
        result = site_settings(request)
        assert "site_settings" in result
        assert isinstance(result["site_settings"], dict)

    def test_site_settings_contains_phone(self, rf):
        request = rf.get("/")
        result = site_settings(request)
        # Our autouse mock returns dict with "phone"
        assert "phone" in result["site_settings"]

    def test_site_settings_keys_available(self, rf, site_settings_obj):
        # Verify the result dict has the expected structure from our autouse mock
        request = rf.get("/")
        result = site_settings(request)
        assert "site_settings" in result
        assert "company_name" in result["site_settings"]


@pytest.mark.unit
class TestStaticContentContextProcessor:
    def test_returns_content_dict(self, rf):
        request = rf.get("/")
        request.LANGUAGE_CODE = "de"
        result = static_content(request)
        assert "content" in result
        assert isinstance(result["content"], dict)

    def test_caches_content_on_second_call(self, rf):
        from features.system.models import StaticTranslation

        StaticTranslation.objects.create(key="hero_title", text_de="Willkommen", text_en="Welcome")
        request = rf.get("/")
        request.LANGUAGE_CODE = "de"
        result1 = static_content(request)
        result2 = static_content(request)
        assert result1["content"] == result2["content"]

    def test_returns_empty_dict_on_programming_error(self, rf):
        from django.core.cache import cache
        from django.db.utils import ProgrammingError

        cache.clear()  # prevent stale cached translations from other tests
        request = rf.get("/")
        request.LANGUAGE_CODE = "de"
        with patch("features.system.context_processors.StaticTranslation.objects") as mock_qs:
            mock_qs.all.side_effect = ProgrammingError("table missing")
            result = static_content(request)
        assert result["content"] == {}


@pytest.mark.unit
class TestActivePromoContextProcessor:
    def test_returns_none_when_no_promo(self, rf):
        from features.promos.context_processors import active_promo

        request = rf.get("/")
        result = active_promo(request)
        assert result["active_promo"] is None

    def test_returns_none_for_excluded_page_impressum(self, rf):
        from features.promos.context_processors import active_promo

        request = rf.get("/impressum/")
        result = active_promo(request)
        assert result["active_promo"] is None

    def test_returns_none_for_excluded_page_datenschutz(self, rf):
        from features.promos.context_processors import active_promo

        request = rf.get("/datenschutz/")
        result = active_promo(request)
        assert result["active_promo"] is None

    def test_returns_active_promo_for_home(self, rf):
        from datetime import timedelta

        from django.utils import timezone
        from features.promos.context_processors import active_promo
        from features.promos.models import PromoMessage

        promo = PromoMessage.objects.create(
            title="Test Promo",
            description="desc",
            is_active=True,
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=1),
            target_pages="",
        )
        request = rf.get("/")
        result = active_promo(request)
        assert result["active_promo"] is not None
        assert result["active_promo"].pk == promo.pk

    def test_returns_none_when_promo_inactive_flag(self, rf):
        from datetime import timedelta

        from django.utils import timezone
        from features.promos.context_processors import active_promo
        from features.promos.models import PromoMessage

        PromoMessage.objects.create(
            title="Inactive Promo",
            description="desc",
            is_active=False,
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=1),
        )
        request = rf.get("/")
        result = active_promo(request)
        assert result["active_promo"] is None
