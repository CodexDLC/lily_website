from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from features.conversations.models import Message
from features.conversations.views.contact import ContactFormView
from system.models import Client


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestContactFormView:
    @patch("features.conversations.services.notify_new_message")
    def test_form_valid_regular(self, mock_notify, rf):
        request = rf.post(
            "/contact/",
            data={
                "sender_name": "John",
                "sender_email": "john@example.com",
                "subject": "Hello",
                "body": "Test message",
            },
        )
        request.user = MagicMock()
        request.user.is_authenticated = False

        view = ContactFormView()
        view.request = request

        mock_form = MagicMock()
        mock_form.cleaned_data = {
            "sender_name": "John",
            "sender_email": "john@example.com",
            "subject": "Hello",
            "body": "Test message",
            "consent_marketing": False,
        }
        mock_message = MagicMock()
        mock_form.save.return_value = mock_message

        response = view.form_valid(mock_form)

        assert response.status_code == 302
        assert "?sent=1" in response.url
        assert mock_message.source == Message.Source.CONTACT_FORM
        mock_notify.assert_called_once_with(mock_message)

    @patch("features.conversations.services.notify_new_message")
    def test_form_valid_htmx(self, mock_notify, rf):
        request = rf.post("/contact/", data={}, HTTP_HX_REQUEST="true")
        request.user = MagicMock()
        request.user.is_authenticated = False

        view = ContactFormView()
        view.request = request

        mock_form = MagicMock()
        mock_form.cleaned_data = {"sender_email": "test@test.com"}
        mock_message = MagicMock()
        mock_form.save.return_value = mock_message

        response = view.form_valid(mock_form)

        assert response.status_code == 200
        assert response.template_name == "features/conversations/partials/success_message.html"

    @patch("features.conversations.services.notify_new_message")
    def test_form_valid_marketing_consent(self, mock_notify, rf):
        client = Client.objects.create(email="john@example.com", first_name="John")
        request = rf.post("/contact/", data={})
        request.user = MagicMock()
        request.user.is_authenticated = False

        view = ContactFormView()
        view.request = request

        mock_form = MagicMock()
        mock_form.cleaned_data = {"sender_email": "john@example.com", "consent_marketing": True}
        mock_message = MagicMock()
        mock_form.save.return_value = mock_message

        view.form_valid(mock_form)

        client.refresh_from_db()
        assert client.consent_marketing is True
        assert client.consent_date is not None

    def test_form_invalid_htmx(self, rf):
        request = rf.post("/contact/", data={}, HTTP_HX_REQUEST="true")
        view = ContactFormView()
        view.request = request

        mock_form = MagicMock()
        response = view.form_invalid(mock_form)

        assert response.status_code == 422
        assert response.template_name == "features/conversations/partials/form.html"

    def test_get_context_data_sent(self, rf):
        request = rf.get("/contact/?sent=1")
        view = ContactFormView()
        view.request = request
        view.kwargs = {}

        context = view.get_context_data()
        assert context["sent"] is True
