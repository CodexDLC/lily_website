from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast

from cabinet.services.client import ClientService
from django.contrib.auth import get_user_model
from django.utils import timezone
from features.booking.models import Appointment
from system.models import Client, UserProfile
from system.selectors.users import UserSelector
from system.services.loyalty import LoyaltyService


def _user_with_profile(username: str = "loyalty-user") -> tuple[object, UserProfile]:
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username, email=f"{username}@test.local")
    profile = UserProfile.objects.create(user=user, first_name="Anna", last_name="Client", source="booking")
    return user, profile


def _link_client(user: object, client: Client) -> Client:
    client.user = user
    client.is_ghost = False
    client.status = Client.STATUS_ACTIVE
    client.save(update_fields=["user", "is_ghost", "status", "updated_at"])
    return client


def _appointment(client: Client, master, service, **overrides) -> Appointment:
    defaults = {
        "client": client,
        "master": master,
        "service": service,
        "datetime_start": timezone.now() - timedelta(days=7),
        "duration_minutes": service.duration,
        "price": service.price,
        "status": Appointment.STATUS_COMPLETED,
    }
    defaults.update(overrides)
    return Appointment.objects.create(**defaults)


def test_loyalty_profile_created_without_client():
    _user, profile = _user_with_profile()

    loyalty = LoyaltyService.get_or_refresh_for_profile(profile)
    display = LoyaltyService.get_display_data(loyalty)

    assert loyalty.profile == profile
    assert loyalty.level == 1
    assert loyalty.progress_percent == 0
    assert loyalty.stats["appointment_count"] == 0
    assert display.level == 1
    assert display.progress_percent == 0


def test_completed_appointments_use_actual_price_for_paid_spend(client_obj, master, service):
    user, profile = _user_with_profile("actual-price")
    _link_client(user, client_obj)
    _appointment(client_obj, master, service, price=Decimal("50.00"), price_actual=Decimal("120.00"))

    loyalty = LoyaltyService.get_or_refresh_for_profile(profile)

    assert loyalty.stats["paid_spend"] == "120.00"
    assert loyalty.effective_spend_score > Decimal("120.00")


def test_behavior_multiplier_uses_positive_and_negative_events(client_obj, master, service):
    user, profile = _user_with_profile("behavior")
    _link_client(user, client_obj)
    _appointment(client_obj, master, service, datetime_start=timezone.now() - timedelta(days=20))
    _appointment(client_obj, master, service, datetime_start=timezone.now() - timedelta(days=10))
    _appointment(
        client_obj,
        master,
        service,
        status=Appointment.STATUS_NO_SHOW,
        datetime_start=timezone.now() - timedelta(days=5),
    )
    _appointment(
        client_obj,
        master,
        service,
        status=Appointment.STATUS_CANCELLED,
        cancel_reason=Appointment.CANCEL_REASON_CLIENT,
        cancelled_at=timezone.now() - timedelta(hours=5),
        datetime_start=timezone.now() - timedelta(hours=1),
    )
    _appointment(
        client_obj,
        master,
        service,
        status=Appointment.STATUS_PENDING,
        datetime_start=timezone.now() - timedelta(days=1),
    )
    _appointment(
        client_obj,
        master,
        service,
        status=Appointment.STATUS_RESCHEDULE_PROPOSED,
        datetime_start=timezone.now() - timedelta(days=2),
    )

    loyalty = LoyaltyService.get_or_refresh_for_profile(profile)

    assert Decimal("0.70") <= loyalty.behavior_multiplier <= Decimal("1.30")
    assert loyalty.stats["completed_count"] == 2
    assert loyalty.stats["no_show_count"] == 1
    assert loyalty.stats["late_cancel_count"] == 1
    assert loyalty.stats["overdue_pending_count"] == 1
    assert loyalty.stats["reschedule_count"] == 1


def test_level_thresholds_and_progress():
    assert LoyaltyService._level_and_progress(Decimal("0")) == (1, 0)
    assert LoyaltyService._level_and_progress(Decimal("200")) == (2, 0)
    assert LoyaltyService._level_and_progress(Decimal("500")) == (3, 0)
    assert LoyaltyService._level_and_progress(Decimal("1000")) == (4, 100)
    assert LoyaltyService._level_and_progress(Decimal("350")) == (2, 50)


def test_source_hash_skips_unchanged_writes_and_updates_on_change(client_obj, master, service):
    user, profile = _user_with_profile("cache")
    _link_client(user, client_obj)
    appt = _appointment(client_obj, master, service)

    loyalty = LoyaltyService.get_or_refresh_for_profile(profile)
    first_hash = loyalty.source_hash
    first_updated_at = loyalty.updated_at

    loyalty = LoyaltyService.get_or_refresh_for_profile(profile)
    assert loyalty.source_hash == first_hash
    assert loyalty.updated_at == first_updated_at

    appt.status = Appointment.STATUS_NO_SHOW
    appt.save(update_fields=["status", "updated_at"])

    loyalty = LoyaltyService.get_or_refresh_for_profile(profile)
    assert loyalty.source_hash != first_hash
    assert loyalty.stats["no_show_count"] == 1


def test_client_corner_context_returns_display_only_loyalty(client_obj, master, service):
    user, _profile = _user_with_profile("corner")
    _link_client(user, client_obj)
    _appointment(client_obj, master, service, price=Decimal("250.00"))

    context = ClientService.get_corner_context(SimpleNamespace(user=user))
    loyalty = context["loyalty"]

    assert loyalty is not None
    assert loyalty.level >= 1
    assert not hasattr(loyalty, "effective_spend_score")
    assert not hasattr(loyalty, "score_points")


def test_client_corner_context_creates_missing_profile_for_registered_client(client_obj, master, service):
    user_model = get_user_model()
    user = user_model.objects.create_user(username="missing-profile", email="missing-profile@test.local")
    _link_client(user, client_obj)
    _appointment(client_obj, master, service, price=Decimal("250.00"))

    context = ClientService.get_corner_context(SimpleNamespace(user=user))

    assert UserProfile.objects.filter(user=user).exists()
    assert context["loyalty"] is not None


def test_user_grid_shows_loyalty_for_registered_users_only(client_obj, master, service):
    user, _profile = _user_with_profile("grid")
    _link_client(user, client_obj)
    _appointment(client_obj, master, service, price=Decimal("250.00"))
    Client.objects.create(first_name="Ghost", phone="+49111000099", is_ghost=True)

    grid = UserSelector.get_users_grid(segment="clients")
    registered = next(item for item in grid.items if item.id == f"user_{cast('Any', user).pk}")
    ghost = next(item for item in grid.items if item.id.startswith("ghost_"))

    assert registered.meta
    assert registered.meta[0][0] == "bi-stars"
    assert "/4" in registered.meta[0][1]
    assert ghost.badge
    assert not any("/4" in text for _icon, text in ghost.meta)
