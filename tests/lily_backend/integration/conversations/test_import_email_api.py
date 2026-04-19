from django.test import RequestFactory, override_settings
from features.conversations.api.import_email import InboundEmailPayload, import_email
from features.conversations.models import Message


@override_settings(CONVERSATIONS_IMPORT_API_KEY="mail-token")  # pragma: allowlist secret
def test_import_email_stores_attachment_metadata_as_note(db):
    request = RequestFactory().post(
        "/api/v1/conversations/import-email",
        HTTP_X_INTERNAL_SCOPE="conversations.import",
        HTTP_X_INTERNAL_TOKEN="mail-token",
    )
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
