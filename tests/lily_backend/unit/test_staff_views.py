import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.urls import reverse

from src.lily_backend.cabinet.views.staff import StaffListView, StaffQuickEditView


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
