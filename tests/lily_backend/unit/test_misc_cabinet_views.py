from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.urls import reverse

from src.lily_backend.cabinet.views.ops import WorkerOpsView
from src.lily_backend.cabinet.views.users import ClientDetailView, UserListView


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


@pytest.mark.django_db
def test_user_list_view(rf, staff_user):
    url = reverse("cabinet:users_list")
    request = rf.get(url)
    request.user = staff_user

    with patch("src.lily_backend.cabinet.views.users.UserService.get_list_context") as mock_ctx:
        mock_ctx.return_value = {}
        view = UserListView.as_view()
        response = view(request)

    assert response.status_code == 200
    assert request.cabinet_module == "users"


@pytest.mark.django_db
def test_client_detail_view(rf, staff_user):
    url = reverse("cabinet:user_modal", kwargs={"id_token": "test-token"})
    request = rf.get(url)
    request.user = staff_user

    with patch("src.lily_backend.cabinet.views.users.UserService.get_client_detail") as mock_detail:
        mock_detail.return_value = {}
        view = ClientDetailView.as_view()
        response = view(request, id_token="test-token")

    assert response.status_code == 200


def test_worker_ops_view(rf, staff_user):
    url = reverse("cabinet:ops_workers")
    request = rf.get(url)
    request.user = staff_user

    with patch("src.lily_backend.cabinet.views.ops.WorkerOpsService") as mock_service_cls:
        mock_service_cls.return_value.summary.return_value = {}
        view = WorkerOpsView.as_view()
        response = view(request)

    assert response.status_code == 200
    assert request.cabinet_module == "ops"
