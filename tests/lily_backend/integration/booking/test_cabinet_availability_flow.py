from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from features.booking.booking_settings import BookingSettings
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


def test_cabinet_slots_allow_same_day_when_book_only_from_next_day_enabled(
    service, master, booking_settings, site_settings_obj
):
    service.masters.add(master)
    booking_settings.book_only_from_next_day = True
    booking_settings.save(update_fields=["book_only_from_next_day"])

    client = Client()
    client.force_login(_make_staff_user())

    response = client.get(
        reverse("cabinet:booking_fetch_slots"),
        {
            "date": timezone.localdate().isoformat(),
            "service_ids": str(service.id),
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["slots"]


def test_booking_settings_page_exposes_owner_controls(site_settings_obj):
    client = Client()
    client.force_login(_make_staff_user())

    response = client.get(reverse("cabinet:booking_settings"))

    assert response.status_code == 200
    assert b"load_strategy" in response.content
    assert b"book_only_from_next_day" in response.content


def test_booking_settings_post_persists_manual_hours_from_cabinet(site_settings_obj):
    settings = BookingSettings.load()
    settings.work_end_saturday = timezone.datetime.strptime("14:00", "%H:%M").time()
    settings.save(update_fields=["work_end_saturday"])

    client = Client()
    client.force_login(_make_staff_user())

    response = client.post(
        reverse("cabinet:booking_settings"),
        {
            key: value
            for key, value in {
                "step_minutes": settings.step_minutes,
                "default_buffer_between_minutes": settings.default_buffer_between_minutes,
                "min_advance_minutes": settings.min_advance_minutes,
                "max_advance_days": settings.max_advance_days,
                "monday_is_closed": "",
                "work_start_monday": settings.work_start_monday.strftime("%H:%M"),
                "work_end_monday": settings.work_end_monday.strftime("%H:%M"),
                "tuesday_is_closed": "",
                "work_start_tuesday": settings.work_start_tuesday.strftime("%H:%M"),
                "work_end_tuesday": settings.work_end_tuesday.strftime("%H:%M"),
                "wednesday_is_closed": "",
                "work_start_wednesday": settings.work_start_wednesday.strftime("%H:%M"),
                "work_end_wednesday": settings.work_end_wednesday.strftime("%H:%M"),
                "thursday_is_closed": "",
                "work_start_thursday": settings.work_start_thursday.strftime("%H:%M"),
                "work_end_thursday": settings.work_end_thursday.strftime("%H:%M"),
                "friday_is_closed": "",
                "work_start_friday": settings.work_start_friday.strftime("%H:%M"),
                "work_end_friday": settings.work_end_friday.strftime("%H:%M"),
                "saturday_is_closed": "",
                "work_start_saturday": settings.work_start_saturday.strftime("%H:%M"),
                "work_end_saturday": "18:00",
                "sunday_is_closed": "on",
                "load_strategy": settings.load_strategy,
                "book_only_from_next_day": "on" if settings.book_only_from_next_day else None,
            }.items()
            if value is not None
        },
    )

    settings.refresh_from_db()

    assert response.status_code == 302
    assert settings.work_end_saturday.strftime("%H:%M") == "18:00"
