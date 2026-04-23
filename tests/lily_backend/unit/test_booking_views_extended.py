from unittest.mock import patch

import pytest
from cabinet.views.booking import (
    BookingActionView,
    BookingCreateView,
    BookingListView,
    BookingModalView,
    BookingScheduleView,
    BookingSettingsForm,
    BookingSettingsView,
    NewBookingView,
)
from django.contrib.auth.models import User
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import RequestFactory
from django.urls import reverse


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def staff_user():
    return User.objects.create_user(username="staff", is_staff=True)


@pytest.fixture
def mock_request(rf, staff_user):
    request = rf.get("/")
    request.user = staff_user
    request._messages = CookieStorage(request)
    request.session = {}
    return request


@pytest.mark.django_db
class TestBookingListView:
    def test_get_full_template(self, mock_request):
        view = BookingListView()
        view.request = mock_request
        templates = view.get_template_names()
        assert "cabinet/booking/list.html" in templates

    def test_get_partial_template_hx(self, rf, staff_user):
        request = rf.get("/", HTTP_HX_REQUEST="true")
        request.user = staff_user
        view = BookingListView()
        view.request = request
        templates = view.get_template_names()
        assert "cabinet/booking/partials/_appointments_panel.html" in templates

    @patch("cabinet.views.booking.BookingService.get_list_context")
    def test_get_context_data(self, mock_get_list, mock_request):
        mock_get_list.return_value = {"appointments": []}
        view = BookingListView()
        view.request = mock_request
        view.kwargs = {"status": "confirmed"}
        context = view.get_context_data()
        assert context["current_status"] == "confirmed"
        mock_get_list.assert_called_once_with(mock_request, status="confirmed")


@pytest.mark.django_db
class TestBookingScheduleView:
    @patch("cabinet.views.booking.BookingService.get_schedule_context")
    def test_get_context_data(self, mock_get_sched, mock_request):
        mock_get_sched.return_value = {"events": []}
        view = BookingScheduleView()
        view.request = mock_request
        context = view.get_context_data()
        assert "events" in context
        mock_get_sched.assert_called_once()


@pytest.mark.django_db
class TestNewBookingView:
    @patch("cabinet.views.booking.BookingService.get_new_booking_context")
    def test_get_context_data(self, mock_get_context, mock_request):
        mock_get_context.return_value = {"services": []}
        view = NewBookingView()
        view.request = mock_request
        context = view.get_context_data()
        assert "services" in context


@pytest.mark.django_db
class TestBookingCreateView:
    @patch("cabinet.views.booking.BookingService.create_new_booking")
    def test_post_redirects(self, mock_create, rf, staff_user):
        mock_create.return_value = {"target_url": "/success/"}
        request = rf.post("/")
        request.user = staff_user
        view = BookingCreateView.as_view()
        response = view(request)
        assert response.status_code == 302
        assert response.url == "/success/"


@pytest.mark.django_db
class TestBookingModalView:
    @patch("cabinet.views.booking.BookingService.get_booking_modal_context")
    def test_get_context_data(self, mock_get_modal, mock_request):
        mock_get_modal.return_value = {"booking": {}}
        view = BookingModalView()
        view.request = mock_request
        view.kwargs = {"pk": 123}
        context = view.get_context_data()
        assert "booking" in context
        mock_get_modal.assert_called_once_with(mock_request, 123)


@pytest.mark.django_db
class TestBookingActionView:
    @patch("cabinet.views.booking.BookingService.perform_action")
    def test_post_action(self, mock_action, rf, staff_user):
        mock_action.return_value = {"target_url": "/list/"}
        request = rf.post("/")
        request.user = staff_user
        view = BookingActionView.as_view()
        response = view(request, pk=1, action="confirm")
        assert response.status_code == 302
        assert response.url == "/list/"
        mock_action.assert_called_once_with(request, booking_id=1, action="confirm")


@pytest.mark.django_db
class TestBookingSettingsView:
    @patch("cabinet.views.booking.BookingService.get_or_create_settings")
    def test_get_settings(self, mock_get_settings, mock_request):
        from features.booking.booking_settings import BookingSettings

        mock_get_settings.return_value = (BookingSettings(), None)
        view = BookingSettingsView.as_view()
        response = view(mock_request)
        assert response.status_code == 200

    @patch("cabinet.views.booking.BookingService.get_or_create_settings")
    def test_post_valid_settings(self, mock_get_settings, rf, staff_user):
        from features.booking.booking_settings import BookingSettings

        mock_get_settings.return_value = (BookingSettings(), None)
        request = rf.post("/", data={"step_minutes": 30, "min_advance_minutes": 60})
        request.user = staff_user
        request._messages = CookieStorage(request)

        with (
            patch.object(BookingSettingsForm, "is_valid", return_value=True),
            patch.object(BookingSettingsForm, "save"),
        ):
            view = BookingSettingsView.as_view()
            response = view(request)
            assert response.status_code == 302
            assert response.url == reverse("cabinet:booking_settings")

    @patch("cabinet.views.booking.BookingService.get_or_create_settings")
    def test_post_with_storage_warning(self, mock_get_settings, rf, staff_user):
        from features.booking.booking_settings import BookingSettings

        mock_get_settings.return_value = (BookingSettings(), "Out of space")
        request = rf.post("/")
        request.user = staff_user
        request._messages = CookieStorage(request)

        view = BookingSettingsView.as_view()
        response = view(request)
        assert response.status_code == 200
        # Check if warning is in messages
        msgs = [m.message for m in request._messages]
        assert "Out of space" in msgs

    @patch("cabinet.views.booking.BookingService.get_or_create_settings")
    def test_post_invalid_settings(self, mock_get_settings, rf, staff_user):
        from features.booking.booking_settings import BookingSettings

        mock_get_settings.return_value = (BookingSettings(), None)
        request = rf.post("/", data={"step_minutes": "invalid"})
        request.user = staff_user
        request._messages = CookieStorage(request)

        view = BookingSettingsView.as_view()
        response = view(request)
        assert response.status_code == 200
        assert "form" in response.context_data
