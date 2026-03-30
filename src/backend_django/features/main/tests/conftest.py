"""Shared fixtures for main app tests."""

import pytest


@pytest.fixture(autouse=True)
def static_translations():
    """
    Create minimal StaticTranslation records so that templates using
    {{ content.some_key }} do not KeyError during tests.

    Also clears the Django cache before each test to prevent the static_content
    context processor from returning a stale empty dict cached by a prior test.
    """
    from django.core.cache import cache

    cache.clear()

    from features.system.models import StaticTranslation

    keys = [
        "service_detail_subtitle",
        "services_hero_title",
        "services_hero_subtitle",
        "home_hero_title",
        "home_hero_subtitle",
        "contacts_hero_title",
        "team_hero_title",
        "faq_hero_title",
    ]
    for key in keys:
        StaticTranslation.objects.get_or_create(key=key, defaults={"text": "", "text_de": "", "text_en": ""})
