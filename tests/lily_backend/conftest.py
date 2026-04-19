"""
Root conftest for lily_backend pytest suite.

Provides shared fixtures used across all feature tests.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.utils import timezone


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Allow DB access in every test without explicit @pytest.mark.django_db."""
    pass


@pytest.fixture(autouse=True)
def mock_redis_settings_sync():
    """
    Patch all codex-django/codex-platform Redis sync calls triggered by model saves.
    SiteSettings and BookingSettings both call async Redis on save — no-op in tests.
    """
    noop = AsyncMock(return_value=None)
    with (
        patch(
            "codex_django.core.redis.managers.settings.DjangoSiteSettingsManager.asave_instance",
            noop,
        ),
        patch(
            "codex_django.core.redis.managers.settings.DjangoSiteSettingsManager.aload_cached",
            AsyncMock(return_value=None),
        ),
        patch(
            "codex_django.core.redis.managers.settings.DjangoSiteSettingsManager.load_cached",
            MagicMock(return_value=None),
        ),
        patch(
            "codex_platform.redis_service.operations.string.StringOperations.set",
            noop,
        ),
        patch(
            "codex_platform.redis_service.operations.string.StringOperations.get",
            AsyncMock(return_value=None),
        ),
        patch(
            "codex_platform.redis_service.operations.hash.HashOperations.get_all",
            AsyncMock(return_value={}),
        ),
        patch(
            "codex_platform.redis_service.operations.hash.HashOperations.get_field",
            AsyncMock(return_value=None),
        ),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_seo_redis():
    """Patch SeoRedisManager to prevent RedisConnectionError in tests."""

    with patch("codex_django.core.redis.managers.seo.SeoRedisManager.aget_page", new_callable=AsyncMock) as m:
        m.return_value = None
        yield m


# ---------------------------------------------------------------------------
# Booking core fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def booking_settings():
    from features.booking.booking_settings import BookingSettings

    obj, _ = BookingSettings.objects.get_or_create(
        pk=1,
        defaults={
            "step_minutes": 30,
            "min_advance_minutes": 0,
            "max_advance_days": 60,
            "default_buffer_between_minutes": 0,
            "monday_is_closed": False,
            "work_start_monday": timezone.datetime.strptime("09:00", "%H:%M").time(),
            "work_end_monday": timezone.datetime.strptime("18:00", "%H:%M").time(),
            "tuesday_is_closed": False,
            "work_start_tuesday": timezone.datetime.strptime("09:00", "%H:%M").time(),
            "work_end_tuesday": timezone.datetime.strptime("18:00", "%H:%M").time(),
            "wednesday_is_closed": False,
            "work_start_wednesday": timezone.datetime.strptime("09:00", "%H:%M").time(),
            "work_end_wednesday": timezone.datetime.strptime("18:00", "%H:%M").time(),
            "thursday_is_closed": False,
            "work_start_thursday": timezone.datetime.strptime("09:00", "%H:%M").time(),
            "work_end_thursday": timezone.datetime.strptime("18:00", "%H:%M").time(),
            "friday_is_closed": False,
            "work_start_friday": timezone.datetime.strptime("09:00", "%H:%M").time(),
            "work_end_friday": timezone.datetime.strptime("18:00", "%H:%M").time(),
            "saturday_is_closed": False,
            "work_start_saturday": timezone.datetime.strptime("10:00", "%H:%M").time(),
            "work_end_saturday": timezone.datetime.strptime("14:00", "%H:%M").time(),
            "sunday_is_closed": True,
        },
    )
    return obj


@pytest.fixture
def site_settings_obj():
    from system.models import SiteSettings

    obj, _ = SiteSettings.objects.get_or_create(pk=1)
    return obj


@pytest.fixture
def category():
    from features.main.models import ServiceCategory

    return ServiceCategory.objects.create(
        name="Test Category",
        slug="test-cat",
        bento_group="nails",
        is_planned=False,
    )


@pytest.fixture
def service(category):
    from features.main.models import Service

    return Service.objects.create(
        category=category,
        name="Test Service",
        slug="test-svc",
        price="50.00",
        duration=60,
        is_active=True,
    )


@pytest.fixture
def master(category):
    """Active Master with full week schedule via MasterWorkingDay."""
    import datetime

    from features.booking.models import Master, MasterWorkingDay

    m = Master.objects.create(
        name="Test Master",
        slug="test-master",
        status=Master.STATUS_ACTIVE,
        work_start=datetime.time(9, 0),
        work_end=datetime.time(18, 0),
        is_public=True,
    )
    m.categories.add(category)

    # Create working days for all week (Mon=0 … Sun=6)
    for weekday in range(7):
        MasterWorkingDay.objects.create(
            master=m,
            weekday=weekday,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(18, 0),
        )

    return m


@pytest.fixture
def client_obj():
    from system.models import Client

    return Client.objects.create(
        first_name="Anna",
        last_name="Testova",
        phone="+49111000001",
        email="anna@test.local",
        status=Client.STATUS_GUEST,
    )


@pytest.fixture
def pending_appointment(client_obj, master, service, booking_settings):
    from features.booking.models import Appointment

    return Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service,
        datetime_start=timezone.now() + timedelta(hours=48),
        duration_minutes=service.duration,
        price=service.price,
        status=Appointment.STATUS_PENDING,
    )


@pytest.fixture
def confirmed_appointment(client_obj, master, service, booking_settings):
    from features.booking.models import Appointment

    return Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service,
        datetime_start=timezone.now() + timedelta(hours=48),
        duration_minutes=service.duration,
        price=service.price,
        status=Appointment.STATUS_CONFIRMED,
    )
