import json
from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from src.lily_backend.cabinet.views.services import CategoryStatusToggleView, ServiceQuickEditView, ServicesListView


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
def service():
    s = MagicMock()
    s.pk = 1
    s.save = MagicMock()
    return s


@pytest.fixture
def category():
    c = MagicMock()
    c.pk = 1
    c.is_active = True
    c.save = MagicMock()
    return c


@pytest.mark.django_db
def test_services_list_view(rf, staff_user):
    url = reverse("cabinet:services_list")
    request = rf.get(url)
    request.user = staff_user

    with patch("src.lily_backend.cabinet.views.services.Service.objects.filter") as mock_filter:
        mock_filter.return_value.order_by.return_value = []
        view = ServicesListView.as_view()
        response = view(request)

    assert response.status_code == 200
    assert request.cabinet_module == "catalog"


@pytest.mark.django_db
def test_service_quick_edit_post_valid(rf, staff_user, service):
    url = reverse("cabinet:service_quick_edit", kwargs={"pk": 1})
    data = {"price": 50, "duration": 60}
    request = rf.post(url, data=data)
    request.user = staff_user

    with (
        patch.object(ServiceQuickEditView, "get_object", return_value=service),
        patch("src.lily_backend.cabinet.views.services.ServiceQuickEditForm") as mock_form_cls,
    ):
        mock_form = mock_form_cls.return_value
        mock_form.is_valid.return_value = True
        mock_form.save.return_value = service

        view = ServiceQuickEditView.as_view()
        response = view(request, pk=1)

    assert response.status_code == 200
    assert json.loads(response.content)["status"] == "ok"


@pytest.mark.django_db
def test_category_status_toggle_post(rf, staff_user, category):
    url = reverse("cabinet:service_category_toggle", kwargs={"pk": 1})
    request = rf.post(url, data={"field": "is_active"})
    request.user = staff_user

    with (
        patch("src.lily_backend.cabinet.views.services.get_object_or_404", return_value=category),
        patch("src.lily_backend.cabinet.views.services.render", return_value=HttpResponse("ok")),
    ):
        view = CategoryStatusToggleView.as_view()
        response = view(request, pk=1)

    assert response.status_code == 200
    assert category.is_active is False
    category.save.assert_called_once()
