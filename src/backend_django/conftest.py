"""
Pytest configuration for Django tests.

Configures test database, Redis, and other fixtures.
"""

import os
import sys
import types
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

# Prevent NinjaAPI from raising ConfigError during tests due to multiple imports
os.environ["NINJA_SKIP_REGISTRY"] = "True"

# ---------------------------------------------------------------------------
# Stub optional/missing packages before Django/app code imports them
# ---------------------------------------------------------------------------

# django_ratelimit: rate limiting — disabled in test settings but module must be importable
for _mod_name in ["django_ratelimit", "django_ratelimit.decorators"]:
    if _mod_name not in sys.modules:
        _fake_rl = types.ModuleType(_mod_name)
        _fake_rl.ratelimit = lambda *a, **kw: lambda f: f
        sys.modules[_mod_name] = _fake_rl

User = get_user_model()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This prevents the need to mark every test with @pytest.mark.django_db.
    """
    pass


# ---------------------------------------------------------------------------
# Infrastructure mocks (autouse – prevents external service calls)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_site_settings_redis():
    """
    Patches SiteSettingsManager.load_from_redis so that view tests don't
    attempt a real Redis connection via the site_settings context processor.
    """
    fake_settings = {
        "phone": "+49 000 000 0000",
        "email": "test@test.local",
        "company_name": "Test Salon",
        "address_street": "Teststraße 1",
        "address_postal_code": "10000",
        "address_locality": "Berlin",
    }
    # django_redis may not be installed in CI/test env.
    # Inject a fake module so the import in site_settings_manager doesn't crash,
    # then patch load_from_redis to return our fake dict.
    import sys
    import types

    if "django_redis" not in sys.modules:
        fake_django_redis = types.ModuleType("django_redis")
        fake_django_redis.get_redis_connection = MagicMock(return_value=MagicMock())
        sys.modules["django_redis"] = fake_django_redis

    import importlib

    mod = importlib.import_module("features.system.redis_managers.site_settings_manager")
    with patch.object(mod.SiteSettingsManager, "load_from_redis", return_value=fake_settings):
        yield


# ---------------------------------------------------------------------------
# Shared model fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def booking_settings():
    """Singleton BookingSettings with test-friendly defaults (no min advance)."""
    from features.booking.models.booking_settings import BookingSettings

    obj, _ = BookingSettings.objects.get_or_create(
        pk=1,
        defaults={
            "default_step_minutes": 30,
            "default_min_advance_minutes": 0,
            "default_max_advance_days": 60,
            "default_buffer_between_minutes": 0,
        },
    )
    return obj


@pytest.fixture
def category():
    """Test Category (nails group, active, no image required for ORM insert)."""
    from features.main.models.category import Category

    return Category.objects.create(
        title="Test Category",
        slug="test-cat",
        bento_group="nails",
        is_active=True,
    )


@pytest.fixture
def service(category):
    """Test Service linked to test category."""
    from features.main.models.service import Service

    return Service.objects.create(
        category=category,
        title="Test Service",
        slug="test-svc",
        price="50.00",
        duration=60,
        is_active=True,
    )


@pytest.fixture
def master(category):
    """Active test Master with full work schedule."""
    from features.booking.models.master import Master

    m = Master.objects.create(
        name="Test Master",
        slug="test-master",
        status=Master.STATUS_ACTIVE,
        work_days=[0, 1, 2, 3, 4, 5, 6],
        is_public=True,
    )
    m.categories.add(category)
    return m


@pytest.fixture
def client_obj():
    """Test Client (ghost pattern, has phone + email)."""
    from features.booking.models.client import Client

    return Client.objects.create(
        first_name="Anna",
        last_name="Testova",
        phone="+49111000001",
        email="anna@test.local",
        status=Client.STATUS_GUEST,
    )


@pytest.fixture
def admin_user():
    """Superuser for cabinet admin tests."""
    return User.objects.create_superuser(
        username="admin_root",
        email="admin@test.local",
        password="testpass123",  # nosec B106  # pragma: allowlist secret
    )


@pytest.fixture
def master_user(category):
    """Regular user linked to a master (for cabinet access tests)."""
    from features.booking.models.master import Master

    user = User.objects.create_user(
        username="master_user",
        email="master@test.local",
        password="testpass123",  # nosec B106  # pragma: allowlist secret
        is_staff=False,
    )
    m = Master.objects.create(
        name="Master User",
        slug="master-user",
        status=Master.STATUS_ACTIVE,
        work_days=[0, 1, 2, 3, 4, 5, 6],
        user=user,
    )
    m.categories.add(category)
    return user


@pytest.fixture
def pending_appointment(client_obj, master, service, booking_settings):
    """Pending Appointment 48 hours in the future."""
    from features.booking.models.appointment import Appointment

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
    """Confirmed Appointment 48 hours in the future."""
    from features.booking.models.appointment import Appointment

    return Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service,
        datetime_start=timezone.now() + timedelta(hours=48),
        duration_minutes=service.duration,
        price=service.price,
        status=Appointment.STATUS_CONFIRMED,
    )


@pytest.fixture
def site_settings_obj():
    """Ensure SiteSettings singleton exists in DB."""
    from features.system.models.site_settings import SiteSettings

    obj, _ = SiteSettings.objects.get_or_create(pk=1)
    return obj


# ---------------------------------------------------------------------------
# Notification / ARQ mocks
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_notifications():
    """
    Patches all NotificationService public send_* methods to no-ops.
    Also resets the singleton before/after each test.
    """
    import features.system.services.notification as notif_module

    notif_module._engine = None

    mock_methods = [
        "send_booking_receipt",
        "send_booking_confirmation",
        "send_booking_cancellation",
        "send_booking_no_show",
        "send_booking_reschedule",
        "send_group_booking_confirmation",
        "send_contact_receipt",
    ]

    patches = []
    mocks = {}
    for method in mock_methods:
        p = patch.object(
            notif_module.NotificationService,
            method,
            return_value=None,
        )
        mocks[method] = p.start()
        patches.append(p)

    yield mocks

    for p in patches:
        p.stop()
    notif_module._engine = None


@pytest.fixture
def mock_arq():
    """Patches DjangoArqClient.enqueue_job to prevent real ARQ queue calls."""
    with patch("core.arq.client.DjangoArqClient.enqueue_job", return_value=MagicMock()) as m:
        yield m
