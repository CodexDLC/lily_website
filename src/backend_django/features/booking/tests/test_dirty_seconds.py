from datetime import datetime

import pytest
from codex_tools.booking.adapters import DjangoAvailabilityAdapter
from codex_tools.booking.slot_calculator import SlotCalculator
from django.utils import timezone
from features.booking.models import Appointment, BookingSettings, Master, MasterDayOff
from features.main.models import Service
from features.system.models.site_settings import SiteSettings


@pytest.mark.django_db
def test_dirty_seconds_handling():
    """
    Проверяет, что адаптер корректно очищает микросекунды из БД.
    Если не очищать, SlotCalculator может найти микро-щель или сломаться.
    """
    # 1. Setup
    master = Master.objects.create(
        name="Test Master",
        work_days=[0, 1, 2, 3, 4, 5, 6],
        work_start=datetime.strptime("09:00", "%H:%M").time(),
        work_end=datetime.strptime("18:00", "%H:%M").time(),
        status=Master.STATUS_ACTIVE,
    )

    # Создаем "грязную" запись: 10:00:00.123456
    dirty_start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=123456)
    target_date = dirty_start.date()

    # Убедимся что дата совпадает с work_days мастера (сегодня)
    # Если сегодня не рабочий день (вдруг), тест упадет, но мы задали work_days=[0..6]

    service = Service.objects.create(title="Test Service", duration=60, price=100)

    Appointment.objects.create(
        master=master,
        service=service,
        client_id=1,  # Mock client ID if needed, or create real client
        datetime_start=dirty_start,
        duration_minutes=60,
        status=Appointment.STATUS_CONFIRMED,
    )

    # 2. Init Adapter
    adapter = DjangoAvailabilityAdapter(
        master_model=Master,
        appointment_model=Appointment,
        service_model=Service,
        day_off_model=MasterDayOff,
        booking_settings_model=BookingSettings,
        site_settings_model=SiteSettings,
        step_minutes=30,
    )

    # 3. Get Availability
    availability = adapter.build_masters_availability([master.pk], target_date)
    master_avail = availability.get(str(master.pk))

    assert master_avail is not None

    # 4. Assertions
    # Ожидаем, что занятый интервал будет ровно 10:00 - 11:00 (без микросекунд)
    # Значит свободные окна: 09:00-10:00 и 11:00-18:00

    windows = master_avail.free_windows

    # Проверяем первое окно (до записи)
    # Если бы микросекунды остались, окно могло бы быть 09:00 - 10:00:00.123456
    first_window_end = windows[0][1]
    assert first_window_end.microsecond == 0
    assert first_window_end.second == 0
    assert first_window_end.minute == 0
    assert first_window_end.hour == 10

    # Проверяем второе окно (после записи)
    # Если бы микросекунды остались, окно началось бы в 11:00:00.123456
    second_window_start = windows[1][0]
    assert second_window_start.microsecond == 0
    assert second_window_start.second == 0
    assert second_window_start.minute == 0
    assert second_window_start.hour == 11

    # Проверяем что калькулятор находит слот ровно в 11:00
    calc = SlotCalculator(step_minutes=30)
    slots = calc.find_slots_in_window(second_window_start, windows[1][1], duration_minutes=60)

    assert len(slots) > 0
    assert slots[0].hour == 11
    assert slots[0].minute == 0
    assert slots[0].microsecond == 0
