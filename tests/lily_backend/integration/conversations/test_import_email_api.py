from unittest.mock import patch

from django.test import RequestFactory, override_settings
from features.conversations.api.import_email import InboundEmailPayload, import_email
from features.conversations.models import Message


def _import_request():
    return RequestFactory().post(
        "/api/v1/conversations/import-email",
        HTTP_X_INTERNAL_SCOPE="conversations.import",
        HTTP_X_INTERNAL_TOKEN="mail-token",
    )


@override_settings(CONVERSATIONS_IMPORT_API_KEY="mail-token")  # pragma: allowlist secret
def test_import_email_stores_attachment_metadata_as_note(db):
    request = _import_request()
    payload = InboundEmailPayload(
        sender_email="client@example.com",
        subject="Attachment",
        body="See file",
        attachments=[{"filename": "offer.pdf", "content_type": "application/pdf", "size": 10_000}],
    )

    result = import_email(request, payload)

    message = Message.objects.get(pk=result["message_id"])
    assert message.source == Message.Source.EMAIL_IMPORT
    assert "offer.pdf" in message.body
    assert "application/pdf" not in message.body


@override_settings(CONVERSATIONS_IMPORT_API_KEY="mail-token")  # pragma: allowlist secret
def test_import_email_notifies_admin_for_known_booking_client(
    confirmed_appointment,
    django_capture_on_commit_callbacks,
):
    payload = InboundEmailPayload(
        sender_name="Anna Testova",
        sender_email="ANNA@TEST.LOCAL",
        subject="Question about my appointment",
        body="Can I change the color?",
    )

    with (
        patch("features.conversations.services.notifications._get_engine") as get_engine,
        django_capture_on_commit_callbacks(execute=True),
    ):
        result = import_email(_import_request(), payload)

    message = Message.objects.get(pk=result["message_id"])
    get_engine.return_value.dispatch_event.assert_called_once_with(
        "conversations.imported_client_email",
        message,
        confirmed_appointment,
        None,
    )


@override_settings(CONVERSATIONS_IMPORT_API_KEY="mail-token")  # pragma: allowlist secret
def test_import_email_does_not_notify_admin_for_unknown_sender(django_capture_on_commit_callbacks):
    payload = InboundEmailPayload(
        sender_name="Unknown",
        sender_email="unknown@example.com",
        subject="Hello",
        body="Do you have appointments?",
    )

    with (
        patch("features.conversations.services.notifications._get_engine") as get_engine,
        django_capture_on_commit_callbacks(execute=True),
    ):
        import_email(_import_request(), payload)

    get_engine.return_value.dispatch_event.assert_not_called()


@override_settings(CONVERSATIONS_IMPORT_API_KEY="mail-token")  # pragma: allowlist secret
def test_import_email_does_not_notify_admin_for_spam(
    confirmed_appointment,
    django_capture_on_commit_callbacks,
):
    payload = InboundEmailPayload(
        sender_name="Anna Testova",
        sender_email=confirmed_appointment.client.email,
        subject="Spam",
        body="Not relevant",
        spam=True,
    )

    with (
        patch("features.conversations.services.notifications._get_engine") as get_engine,
        django_capture_on_commit_callbacks(execute=True),
    ):
        import_email(_import_request(), payload)

    get_engine.return_value.dispatch_event.assert_not_called()


@override_settings(CONVERSATIONS_IMPORT_API_KEY="mail-token")  # pragma: allowlist secret
def test_import_email_notifies_admin_for_known_client_reply(
    confirmed_appointment,
    django_capture_on_commit_callbacks,
):
    thread = Message.objects.create(
        sender_name="Anna Testova",
        sender_email=confirmed_appointment.client.email,
        subject="Original",
        body="Original body",
        thread_key="thread-1",
    )
    payload = InboundEmailPayload(
        sender_name="Anna Testova",
        sender_email=confirmed_appointment.client.email,
        subject="Re: Original",
        body="Reply body",
        thread_key="thread-1",
    )

    with (
        patch("features.conversations.services.notifications._get_engine") as get_engine,
        django_capture_on_commit_callbacks(execute=True),
    ):
        result = import_email(_import_request(), payload)

    get_engine.return_value.dispatch_event.assert_called_once()
    event_name, message, appointment, reply = get_engine.return_value.dispatch_event.call_args.args
    assert event_name == "conversations.imported_client_email"
    assert message == thread
    assert appointment == confirmed_appointment
    assert reply.pk == result["reply_id"]
