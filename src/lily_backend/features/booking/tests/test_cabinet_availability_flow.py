from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone

from features.booking.models import MasterDayOff
from features.booking.services import cabinet as cabinet_module
from features.booking.services.cabinet import get_booking_cabinet_workflow


def _make_staff_user():
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="cabinet-staff",
        email="cabinet-staff@test.local",
        password="test-pass-123",  # pragma: allowlist secret
        is_staff=True,
    )


def test_new_booking_context_starts_without_prefetched_slots(booking_settings):
    booking_settings.max_advance_days = 5
    booking_settings.save(update_fields=["max_advance_days"])
    cabinet_module._cabinet_workflow = None

    request = RequestFactory().get("/cabinet/booking/new/")
    context = get_booking_cabinet_workflow().get_new_booking_context(request)

    assert context["picker"].default_date == ""
    assert context["picker"].slot_matrix_json == "{}"
    assert context["picker"].available_days


def test_fetch_days_returns_empty_when_horizon_is_fully_blocked(service, master, booking_settings, site_settings_obj):
    booking_settings.max_advance_days = 2
    booking_settings.save(update_fields=["max_advance_days"])

    today = timezone.localdate()
    MasterDayOff.objects.create(master=master, date=today)
    MasterDayOff.objects.create(master=master, date=today + timedelta(days=1))

    client = Client()
    client.force_login(_make_staff_user())

    response = client.get(reverse("cabinet:booking_fetch_days"), {"service_ids": str(service.id)})

    assert response.status_code == 200
    assert response.json()["available_dates"] == []


def test_fetch_slots_supports_any_master_without_master_id(service, master, booking_settings, site_settings_obj):
    target_date = timezone.localdate() + timedelta(days=1)

    client = Client()
    client.force_login(_make_staff_user())

    response = client.get(
        reverse("cabinet:booking_fetch_slots"),
        {
            "date": target_date.isoformat(),
            "service_ids": str(service.id),
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["master_id"] is None
    assert payload["slots"]
