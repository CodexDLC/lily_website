import datetime as dt
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from src.lily_backend.cabinet.services.staff import StaffService
from src.lily_backend.cabinet.views.staff import StaffDaysOffView, StaffListView, StaffQuickEditView


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def staff_user():
    user = MagicMock()
    user.is_active = True
    user.is_staff = True
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_staff_service():
    with patch("src.lily_backend.cabinet.views.staff.StaffService") as mock:
        yield mock


def test_staff_list_view(rf, staff_user, mock_staff_service):
    url = reverse("cabinet:staff_list")
    request = rf.get(url)
    request.user = staff_user

    mock_staff_service.get_list_context.return_value = {"staff": []}

    view = StaffListView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert request.cabinet_module == "staff"
    mock_staff_service.get_list_context.assert_called_once_with(request)


def test_staff_days_off_view_get(rf, staff_user, mock_staff_service):
    url = reverse("cabinet:staff_days_off")
    request = rf.get(f"{url}?master_id=7&year=2026&month=8")
    request.user = staff_user

    mock_staff_service.get_days_off_context.return_value = {"masters": []}

    view = StaffDaysOffView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert request.cabinet_module == "staff"
    mock_staff_service.get_days_off_context.assert_called_once_with(
        request,
        master_id=7,
        year=2026,
        month=8,
    )


def test_staff_days_off_view_renders_calendar(rf, staff_user, master):
    url = reverse("cabinet:staff_days_off")
    request = rf.get(url)
    request.user = staff_user

    response = StaffDaysOffView.as_view()(request)

    assert response.status_code == 200
    assert master.name in response.rendered_content
    assert 'staff-days-off-form' in response.rendered_content


def test_staff_days_off_view_post(rf, staff_user, mock_staff_service):
    url = reverse("cabinet:staff_days_off")
    request = rf.post(
        url,
        data={
            "master_id": "7",
            "year": "2026",
            "month": "8",
            "dates": ["2026-08-06", "2026-08-07"],
        },
    )
    request.user = staff_user
    mock_staff_service.save_days_off.return_value = {"blocked_dates": []}

    with patch("src.lily_backend.cabinet.views.staff.messages") as mock_messages:
        response = StaffDaysOffView.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"{url}?master_id=7&year=2026&month=8"
    mock_staff_service.save_days_off.assert_called_once_with(
        master_id=7,
        year=2026,
        month=8,
        selected_dates=["2026-08-06", "2026-08-07"],
    )
    mock_messages.success.assert_called_once()


def test_staff_service_save_days_off_syncs_selected_month(master):
    from features.booking.models.schedule import MasterDayOff

    MasterDayOff.objects.create(master=master, date=dt.date(2026, 8, 6))
    MasterDayOff.objects.create(master=master, date=dt.date(2026, 9, 1))

    result = StaffService.save_days_off(
        master_id=master.pk,
        year=2026,
        month=8,
        selected_dates=["2026-08-07", "2026-09-02", "bad-date"],
    )

    dates = set(MasterDayOff.objects.filter(master=master).values_list("date", flat=True))
    assert dt.date(2026, 8, 6) not in dates
    assert dt.date(2026, 8, 7) in dates
    assert dt.date(2026, 9, 1) in dates
    assert dt.date(2026, 9, 2) not in dates
    assert result["created"] == 1
    assert result["deleted"] == 1


def test_staff_service_save_days_off_blocks_dates_with_active_appointments(master, service, client_obj):
    from features.booking.models.appointment import Appointment
    from features.booking.models.schedule import MasterDayOff

    blocked_day = dt.date(2026, 8, 7)
    Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service,
        datetime_start=timezone.make_aware(dt.datetime(2026, 8, 7, 10, 0)),
        duration_minutes=service.duration,
        price=service.price,
        status=Appointment.STATUS_CONFIRMED,
    )

    result = StaffService.save_days_off(
        master_id=master.pk,
        year=2026,
        month=8,
        selected_dates=[blocked_day.isoformat()],
    )

    assert not MasterDayOff.objects.filter(master=master, date=blocked_day).exists()
    assert result["blocked_dates"] == [blocked_day]


def test_staff_quick_edit_post_valid(rf, staff_user):
    url = reverse("cabinet:staff_modal", kwargs={"pk": 1})
    request = rf.post(url, data={"name": "Updated"})
    request.user = staff_user

    master = MagicMock()
    mock_form = MagicMock()
    mock_form.is_valid.return_value = True
    mock_form.save.return_value = master

    view_func = StaffQuickEditView.as_view()
    with (
        patch.object(StaffQuickEditView, "get_object", return_value=master),
        patch.object(StaffQuickEditView, "get_form", return_value=mock_form),
    ):
        response = view_func(request, pk=1)

    assert response.status_code == 200
    assert json.loads(response.content)["status"] == "ok"


def test_staff_quick_edit_post_invalid(rf, staff_user):
    url = reverse("cabinet:staff_modal", kwargs={"pk": 1})
    request = rf.post(url, data={})
    request.user = staff_user

    master = MagicMock()
    mock_form = MagicMock()
    mock_form.is_valid.return_value = False
    mock_form.errors = {"name": ["required"]}

    view_func = StaffQuickEditView.as_view()
    with (
        patch.object(StaffQuickEditView, "get_object", return_value=master),
        patch.object(StaffQuickEditView, "get_form", return_value=mock_form),
    ):
        response = view_func(request, pk=1)

    assert response.status_code == 400
    assert json.loads(response.content)["status"] == "error"
