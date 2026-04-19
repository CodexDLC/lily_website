"""
Integration tests for BookingV2Service.get_available_slots().

Проверяет что сетка слотов:
  - начинается с реального времени начала работы мастера, а не с 8:00
  - показывает все слоты дня при свободных мастерах
  - убирает слот если мастер первой услуги занят в это время
  - скрывает слот если хотя бы один мастер цепочки полностью занят

Run:
    pytest src/backend_django/features/booking/tests/test_v2_slots.py -v
"""

import zoneinfo
from datetime import date, datetime, time, timedelta

import pytest
from django.utils import timezone
from features.booking.models import Appointment
from features.booking.models.booking_settings import BookingSettings
from features.booking.models.client import Client
from features.booking.models.master import Master
from features.booking.models.master_day_off import MasterDayOff
from features.booking.services.v2_booking_service import BookingV2Service
from features.main.models.category import Category
from features.main.models.service import Service
from features.system.models.site_settings import SiteSettings

# ---------------------------------------------------------------------------
# Динамическая дата: берем ближайший понедельник в будущем
# ---------------------------------------------------------------------------
_today = date.today()
MONDAY = _today + timedelta(days=(7 - _today.weekday()) % 7)
if _today >= MONDAY:
    MONDAY += timedelta(days=7)

TEST_TZ = "Europe/Berlin"


@pytest.fixture
def site_settings(db):
    """Салон работает Пн-Пт 10:00-18:00, Сб 10:00-14:00."""
    s = SiteSettings.load()
    s.work_start_weekdays = time(10, 0)
    s.work_end_weekdays = time(18, 0)
    s.work_start_saturday = time(10, 0)
    s.work_end_saturday = time(14, 0)
    s.timezone = TEST_TZ
    s.save()
    return s


@pytest.fixture
def booking_settings(db):
    """Шаг 30 мин, минимум 0 мин заранее (для тестов)."""
    s = BookingSettings.load()
    s.default_step_minutes = 30
    s.default_min_advance_minutes = 0
    s.default_buffer_between_minutes = 0
    s.save()
    return s


@pytest.fixture
def cat_nails(db):
    return Category.objects.create(title="Ногти", slug="nails", is_active=True)


@pytest.fixture
def cat_lashes(db):
    return Category.objects.create(title="Ресницы", slug="lashes", is_active=True)


@pytest.fixture
def cat_brows(db):
    return Category.objects.create(title="Брови", slug="brows", is_active=True)


@pytest.fixture
def svc_manicure(cat_nails):
    return Service.objects.create(
        title="Маникюр",
        slug="manicure",
        category=cat_nails,
        duration=60,
        price="15.00",
        is_active=True,
    )


@pytest.fixture
def svc_lashes(cat_lashes):
    return Service.objects.create(
        title="Наращивание ресниц",
        slug="lashes-ext",
        category=cat_lashes,
        duration=90,
        price="30.00",
        is_active=True,
    )


@pytest.fixture
def svc_brows(cat_brows):
    return Service.objects.create(
        title="Коррекция бровей",
        slug="brow-corr",
        category=cat_brows,
        duration=30,
        price="8.00",
        is_active=True,
    )


def make_master(name, slug, category, work_start=time(10, 0), work_end=time(18, 0)):
    """Создаёт мастера который работает Пн-Вс (0-6)."""
    m = Master.objects.create(
        name=name,
        slug=slug,
        status=Master.STATUS_ACTIVE,
        work_start=work_start,
        work_end=work_end,
        work_days=[0, 1, 2, 3, 4, 5, 6],
        timezone=TEST_TZ,
    )
    m.categories.add(category)
    return m


# ---------------------------------------------------------------------------
# Тесты
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSlotsStartTime:
    """Слоты начинаются с реального времени мастера, не с 08:00."""

    def test_single_service_starts_at_master_work_start(self, site_settings, booking_settings, cat_nails, svc_manicure):
        """1 услуга, мастер 10:00-18:00 → первый слот 10:00."""
        make_master("Аня", "anya", cat_nails, time(10, 0), time(18, 0))
        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id],
            target_date=MONDAY,
        )
        assert slots, f"Слоты должны быть на {MONDAY}"
        assert "10:00" in slots, f"Первый слот должен быть 10:00, получили: {list(slots)[:3]}"
        assert "08:00" not in slots, "08:00 не должен быть в слотах"

    def test_three_services_different_masters_no_early_slots(
        self,
        site_settings,
        booking_settings,
        cat_nails,
        cat_lashes,
        cat_brows,
        svc_manicure,
        svc_lashes,
        svc_brows,
    ):
        """
        3 услуги у 3 разных мастеров.
        Мастера работают с 10:00 → первый слот 10:00.
        """
        make_master("Аня", "anya", cat_nails, time(10, 0), time(18, 0))
        make_master("Маша", "masha", cat_lashes, time(10, 0), time(18, 0))
        make_master("Катя", "katya", cat_brows, time(10, 0), time(18, 0))

        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id, svc_lashes.id, svc_brows.id],
            target_date=MONDAY,
        )

        assert slots, "Слоты должны быть"
        assert "10:00" in slots, f"Первый слот должен быть 10:00, получили: {list(slots)[:5]}"

    def test_master_with_late_start_shifts_slots(self, site_settings, booking_settings, cat_nails, svc_manicure):
        """Мастер начинает в 13:00 → слотов до 13:00 нет."""
        make_master("Вечерняя Аня", "anya-late", cat_nails, time(13, 0), time(20, 0))
        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id],
            target_date=MONDAY,
        )
        assert slots
        assert "13:00" in slots
        assert "10:00" not in slots


@pytest.mark.django_db
class TestSlotsWithBusyMasters:
    """Занятые слоты корректно убираются из сетки."""

    @pytest.fixture(autouse=True)
    def dummy_client(self, db):
        self.client = Client.objects.create(phone="+49000000000")

    def _book_slot(self, master, service, target_date, start_hour, start_min=0):
        """Создаёт запись (занимает слот у мастера) с учетом таймзоны."""
        tz = zoneinfo.ZoneInfo(TEST_TZ)
        dt_start = timezone.make_aware(datetime.combine(target_date, time(start_hour, start_min)), tz)
        return Appointment.objects.create(
            client=self.client,
            master=master,
            service=service,
            datetime_start=dt_start,
            duration_minutes=service.duration,
            status=Appointment.STATUS_CONFIRMED,
            source=Appointment.SOURCE_ADMIN,
        )

    def test_busy_slot_disappears_from_grid(self, site_settings, booking_settings, cat_nails, svc_manicure):
        """Мастер занят в 10:00 → 10:00 нет в сетке, но 11:00 есть."""
        master = make_master("Аня", "anya", cat_nails, time(10, 0), time(18, 0))
        self._book_slot(master, svc_manicure, MONDAY, 10)

        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id],
            target_date=MONDAY,
        )
        assert "10:00" not in slots
        assert "11:00" in slots

    def test_fully_booked_master_no_slots(self, site_settings, booking_settings, cat_nails, svc_manicure):
        """Мастер полностью занят весь день → нет слотов."""
        master = make_master("Аня", "anya", cat_nails, time(10, 0), time(12, 0))
        self._book_slot(master, svc_manicure, MONDAY, 10)
        self._book_slot(master, svc_manicure, MONDAY, 11)

        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id],
            target_date=MONDAY,
        )
        assert not slots

    def test_chain_blocked_when_secondary_master_fully_busy(
        self, site_settings, booking_settings, cat_nails, cat_lashes, svc_manicure, svc_lashes
    ):
        """2 услуги: мастер A свободен, мастер B (2-я услуга) полностью занят."""
        make_master("Аня", "anya", cat_nails, time(10, 0), time(12, 0))
        master_b = make_master("Маша", "masha", cat_lashes, time(10, 0), time(12, 0))
        self._book_slot(master_b, svc_lashes, MONDAY, 10)

        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id, svc_lashes.id],
            target_date=MONDAY,
        )
        assert not slots


@pytest.mark.django_db
class TestSlotsWithMasterSelections:
    """master_selections правильно ограничивает мастеров."""

    def test_specific_master_selected_shows_his_slots_only(
        self, site_settings, booking_settings, cat_nails, svc_manicure
    ):
        anya = make_master("Аня", "anya", cat_nails, time(10, 0), time(18, 0))
        _vera = make_master("Вера", "vera", cat_nails, time(9, 0), time(18, 0))

        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id],
            target_date=MONDAY,
            master_selections={"0": str(anya.pk)},
        )
        assert "10:00" in slots
        assert "09:00" not in slots

    def test_any_master_includes_earliest_available(self, site_settings, booking_settings, cat_nails, svc_manicure):
        _anya = make_master("Аня", "anya", cat_nails, time(10, 0), time(18, 0))
        _vera = make_master("Вера", "vera", cat_nails, time(9, 0), time(18, 0))

        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id],
            target_date=MONDAY,
            master_selections={"0": "any"},
        )
        assert "09:00" in slots
        assert "10:00" in slots


@pytest.mark.django_db
class TestDayOffRespected:
    """MasterDayOff убирает мастера из расчёта."""

    def test_master_on_day_off_no_slots(self, site_settings, booking_settings, cat_nails, svc_manicure):
        master = make_master("Аня", "anya", cat_nails, time(10, 0), time(18, 0))
        MasterDayOff.objects.create(master=master, date=MONDAY)

        svc = BookingV2Service()
        slots = svc.get_available_slots(
            service_ids=[svc_manicure.id],
            target_date=MONDAY,
        )
        assert not slots
