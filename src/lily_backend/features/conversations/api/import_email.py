from __future__ import annotations

from typing import Any

from django.db import transaction
from ninja import Router, Schema

from features.conversations.models import Message, MessageReply

router = Router(tags=["Conversations"])


class AttachmentMetadata(Schema):
    filename: str = ""
    content_type: str = ""
    size: int | None = None
    storage_url: str | None = None


class InboundEmailPayload(Schema):
    sender_name: str = ""
    sender_email: str
    subject: str = ""
    body: str = ""
    text_truncated: bool = False
    oversized: bool = False
    spam: bool = False
    thread_key: str | None = None
    message_id: str = ""
    in_reply_to: str = ""
    references: list[str] = []
    attachments: list[AttachmentMetadata] = []
    raw_size: int | None = None


@router.post("/import-email", summary="Persist one normalized inbound email")
def import_email(request, payload: InboundEmailPayload) -> dict[str, Any]:
    from system.api.auth import require_internal_scope

    require_internal_scope(request, "conversations.import")

    body = _with_attachment_note(
        payload.body,
        attachments=payload.attachments,
        text_truncated=payload.text_truncated,
        oversized=payload.oversized,
    )
    if not body.strip():
        body = "Письмо содержит вложение без текстового содержимого."

    with transaction.atomic():
        thread = _find_thread(payload)
        if thread and not payload.spam:
            reply = MessageReply.objects.create(message=thread, body=body, is_inbound=True)
            thread.status = Message.Status.OPEN
            thread.is_read = False
            thread.save(update_fields=["status", "is_read", "updated_at"])
            return {"status": "reply-created", "message_id": thread.pk, "reply_id": reply.pk}

        message = Message.objects.create(
            sender_name=payload.sender_name or payload.sender_email,
            sender_email=payload.sender_email,
            subject=payload.subject[:500],
            body=body,
            source=Message.Source.EMAIL_IMPORT,
            channel=Message.Channel.EMAIL,
            topic=Message.Topic.GENERAL,
            status=Message.Status.SPAM if payload.spam else Message.Status.OPEN,
            is_read=False,
            admin_notes=_build_admin_notes(payload),
        )
        return {"status": "message-created", "message_id": message.pk, "reply_id": None}


def _find_thread(payload: InboundEmailPayload) -> Message | None:
    if payload.thread_key:
        return Message.objects.filter(thread_key=payload.thread_key).first()
    tokens = [payload.in_reply_to, *payload.references]
    for token in tokens:
        if not token:
            continue
        clean = token.strip("<> ")
        found = Message.objects.filter(thread_key=clean).first()
        if found:
            return found
    return None


def _with_attachment_note(
    body: str,
    *,
    attachments: list[AttachmentMetadata],
    text_truncated: bool,
    oversized: bool,
) -> str:
    notes: list[str] = []
    if attachments:
        rendered = ", ".join(
            f"{item.filename or item.content_type or 'attachment'}"
            f"{f' ({item.size} bytes)' if item.size is not None else ''}"
            for item in attachments
        )
        notes.append(f"Письмо содержало вложения: {rendered}")
    if text_truncated:
        notes.append("Текст письма был обрезан при импорте.")
    if oversized:
        notes.append("Письмо было слишком большим для полного импорта.")
    if not notes:
        return body
    return f"{body.rstrip()}\n\n---\n" + "\n".join(notes)


def _build_admin_notes(payload: InboundEmailPayload) -> str:
    parts = []
    if payload.message_id:
        parts.append(f"Message-ID: {payload.message_id}")
    if payload.raw_size is not None:
        parts.append(f"Raw size: {payload.raw_size}")
    if payload.oversized:
        parts.append("Import status: oversized")
    if payload.spam:
        parts.append("Import status: spam")
    return "\n".join(parts)
