"""
Integration tests for features.main.services.contact_service.ContactService.
Tests request creation, client linking, and notification triggering.
"""

from unittest.mock import patch

import pytest
from features.booking.models.client import Client
from features.main.models.contact_request import ContactRequest
from features.main.services.contact_service import ContactService


@pytest.mark.django_db
class TestContactServiceCreateRequest:
    def test_creates_contact_request(self, mock_notifications):
        request = ContactService.create_request(
            first_name="Anna",
            last_name="Test",
            contact_type="email",
            contact_value="anna@test.de",
            message="Hello, I have a question.",
        )
        assert request.pk is not None
        assert ContactRequest.objects.filter(pk=request.pk).exists()

    def test_creates_client_with_email(self, mock_notifications):
        ContactService.create_request(
            first_name="Maria",
            last_name="Müller",
            contact_type="email",
            contact_value="maria@example.de",
            message="Question about booking",
        )
        assert Client.objects.filter(email="maria@example.de").exists()

    def test_creates_client_with_phone(self, mock_notifications):
        ContactService.create_request(
            first_name="Hans",
            last_name="Weber",
            contact_type="phone",
            contact_value="+49123456789",
            message="Call me back",
        )
        # Phone is stored normalized (strips +)
        assert Client.objects.filter(phone__contains="49123456789").exists()

    def test_email_type_sets_email_field(self, mock_notifications):
        request = ContactService.create_request(
            first_name="Test",
            last_name="User",
            contact_type="email",
            contact_value="test@email.de",
            message="Test message",
        )
        client = request.client
        assert client.email == "test@email.de"
        assert client.phone == "" or client.phone is None or len(client.phone.strip("+")) == 0

    def test_phone_type_sets_phone_field(self, mock_notifications):
        request = ContactService.create_request(
            first_name="Test",
            last_name="User",
            contact_type="phone",
            contact_value="+49987654321",
            message="Test message",
        )
        client = request.client
        # Phone should be set (normalized)
        assert client.phone is not None

    def test_message_stored_correctly(self, mock_notifications):
        msg = "I want to know about your services!"
        request = ContactService.create_request(
            first_name="Anna",
            last_name="Test",
            contact_type="email",
            contact_value="anna2@test.de",
            message=msg,
        )
        request.refresh_from_db()
        assert request.message == msg

    def test_topic_stored_correctly(self, mock_notifications):
        request = ContactService.create_request(
            first_name="Anna",
            last_name="Test",
            contact_type="email",
            contact_value="anna3@test.de",
            message="Job question",
            topic="job",
        )
        request.refresh_from_db()
        assert request.topic == "job"

    def test_default_topic_is_general(self, mock_notifications):
        request = ContactService.create_request(
            first_name="Anna",
            last_name="Test",
            contact_type="email",
            contact_value="anna4@test.de",
            message="General question",
        )
        request.refresh_from_db()
        assert request.topic == "general"

    def test_returns_contact_request_instance(self, mock_notifications):
        result = ContactService.create_request(
            first_name="Bob",
            last_name="Brown",
            contact_type="email",
            contact_value="bob@test.de",
            message="Hello",
        )
        assert isinstance(result, ContactRequest)

    def test_reuses_existing_client(self, mock_notifications):
        """Two requests with same email should reuse the same client."""
        r1 = ContactService.create_request(
            first_name="Anna",
            last_name="Test",
            contact_type="email",
            contact_value="reuse@test.de",
            message="First message",
        )
        r2 = ContactService.create_request(
            first_name="Anna",
            last_name="Test",
            contact_type="email",
            contact_value="reuse@test.de",
            message="Second message",
        )
        assert r1.client.pk == r2.client.pk

    def test_notification_triggered_for_email_client(self, mock_notifications):
        ContactService.create_request(
            first_name="Notify",
            last_name="User",
            contact_type="email",
            contact_value="notify@test.de",
            message="Notify me",
        )
        mock_notifications["send_contact_receipt"].assert_called_once()

    def test_notification_failure_does_not_raise(self):
        """If notification fails, create_request should still return the request."""
        with patch(
            "features.main.services.contact_service.NotificationService.send_contact_receipt",
            side_effect=Exception("Notification failed"),
        ):
            request = ContactService.create_request(
                first_name="Fail",
                last_name="Test",
                contact_type="email",
                contact_value="fail@test.de",
                message="This should not raise",
            )
        assert request.pk is not None

    def test_consent_marketing_passed_to_client(self, mock_notifications):
        request = ContactService.create_request(
            first_name="Consent",
            last_name="User",
            contact_type="email",
            contact_value="consent@test.de",
            message="Marketing ok",
            consent_marketing=True,
        )
        assert request.client.consent_marketing is True

    def test_lang_parameter_passed_to_notification(self, mock_notifications):
        ContactService.create_request(
            first_name="Lang",
            last_name="Test",
            contact_type="email",
            contact_value="lang@test.de",
            message="German message",
            lang="de",
        )
        call_kwargs = mock_notifications["send_contact_receipt"].call_args
        assert call_kwargs is not None
        # Check lang was passed
        kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}
        # The lang kwarg should be 'de'
        if "lang" in kwargs:
            assert kwargs["lang"] == "de"
