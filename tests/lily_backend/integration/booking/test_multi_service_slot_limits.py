from __future__ import annotations

from datetime import date, time, timedelta

from django.utils import timezone
from features.booking.models import MasterWorkingDay
from features.booking.selector.engine import (
    MULTI_SERVICE_MAX_SOLUTIONS,
    MULTI_SERVICE_MAX_UNIQUE_STARTS,
    get_booking_engine_gateway,
)
from features.main.models import Service


def _next_weekday(weekday: int) -> date:
    today = timezone.localdate()
    days_ahead = (weekday - today.weekday() + 7) % 7 or 7
    return today + timedelta(days=days_ahead)


def test_multi_service_slots_are_not_truncated_by_default_limits(
    category,
    booking_settings,
    site_settings_obj,
):
    booking_settings.step_minutes = 30
    booking_settings.default_buffer_between_minutes = 0
    for day_name in ("monday", "tuesday", "wednesday", "thursday", "friday"):
        setattr(booking_settings, f"{day_name}_is_closed", False)
        setattr(booking_settings, f"work_start_{day_name}", time(8, 0))
        setattr(booking_settings, f"work_end_{day_name}", time(18, 0))
    booking_settings.saturday_is_closed = False
    booking_settings.work_start_saturday = time(8, 0)
    booking_settings.work_end_saturday = time(14, 0)
    booking_settings.save()

    weekday_date = _next_weekday(0)
    saturday_date = _next_weekday(5)

    service_one = Service.objects.create(
        name="Chain Service 150",
        slug=f"chain-service-150-{weekday_date.isoformat()}",
        category=category,
        duration=150,
        price=100,
    )
    service_two = Service.objects.create(
        name="Chain Service 60",
        slug=f"chain-service-60-{weekday_date.isoformat()}",
        category=category,
        duration=60,
        price=50,
    )

    from features.booking.models import Master

    masters = []
    for index in (1, 2):
        master = Master.objects.create(
            name=f"Chain Master {index}",
            slug=f"chain-master-{index}-{weekday_date.isoformat()}",
            status=Master.STATUS_ACTIVE,
        )
        MasterWorkingDay.objects.create(
            master=master,
            weekday=0,
            start_time=time(8, 0),
            end_time=time(18, 0),
        )
        MasterWorkingDay.objects.create(
            master=master,
            weekday=5,
            start_time=time(8, 0),
            end_time=time(14, 0),
        )
        master.categories.add(category)
        masters.append(master)

    service_one.masters.add(*masters)
    service_two.masters.add(*masters)

    gateway = get_booking_engine_gateway()

    weekday_slots = gateway.get_available_slots(
        service_ids=[service_one.id, service_two.id],
        target_date=weekday_date,
    ).get_unique_start_times()
    saturday_slots = gateway.get_available_slots(
        service_ids=[service_one.id, service_two.id],
        target_date=saturday_date,
    ).get_unique_start_times()

    assert MULTI_SERVICE_MAX_SOLUTIONS > 50
    assert MULTI_SERVICE_MAX_UNIQUE_STARTS > 50
    assert saturday_slots[-1] == "10:30"
    assert "13:30" in weekday_slots
    assert len(weekday_slots) > len(saturday_slots)
