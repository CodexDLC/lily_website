# Compose-New Email — Bug Analysis and Fix

## What's broken

The Compose form at the conversations cabinet ("Новое сообщение",
visible at the top of the inbox sidebar) submits successfully — DB
records are created — but the recipient never receives the email.
Reply-from-thread and mass-mailing both work; only compose-new is
broken.

### Reproduction (current behavior)

1. Visit `/cabinet/conversations/compose/` (or wherever the inbox's
   Compose entry routes).
2. Fill `Кому` (To), `Тема` (Subject), `Сообщение` (Body).
3. Click `Отправить` (Send).
4. Observe: the page returns success; a `Message` row and a
   `MessageReply` row are inserted into the DB; **no ARQ job is
   enqueued**; **no email is sent**.

### Root cause

`src/lily_backend/features/conversations/services/workflow.py:18-42`
defines `create_manual_message`:

```python
def create_manual_message(*, to_email: str, subject: str, body: str, user: Any) -> Message:
    """Create a manual outbound thread for cabinet compose flow."""
    user_model = get_user_model()
    display_name = user.get_full_name() if isinstance(user, user_model) else ""
    sender_name = display_name or to_email

    with transaction.atomic():
        message = Message.objects.create(
            sender_name=sender_name,
            sender_email=to_email,            # <-- semantic abuse
            subject=subject,
            body=body,
            source=Message.Source.MANUAL,
            channel=Message.Channel.EMAIL,
            topic=Message.Topic.GENERAL,
            status=Message.Status.PROCESSED,
            is_read=True,
        )
        MessageReply.objects.create(
            message=message,
            body=body,
            sent_by=user if getattr(user, "is_authenticated", False) else None,
            is_inbound=False,
        )
    return message       # <-- returns; nothing was dispatched
```

Compare with the working `create_reply` (same file, line 45):

```python
def create_reply(*, message: Message, body: str, user: Any) -> MessageReply:
    """Persist an outbound reply and update the thread state."""
    with transaction.atomic():
        reply = MessageReply.objects.create(
            message=message,
            body=body,
            sent_by=user if getattr(user, "is_authenticated", False) else None,
            is_inbound=False,
        )
        message.status = Message.Status.PROCESSED
        message.is_read = True
        message.save(update_fields=["status", "is_read", "updated_at"])
    notify_thread_reply(message, reply)        # <-- dispatch
    return reply
```

`create_reply` calls `notify_thread_reply()`, which dispatches the
`"conversations.thread_reply"` event through the engine
(`features/conversations/services/alerts.py:37-42`). That event has a
registered handler at `alerts.py:83-94` that produces a
`NotificationDispatchSpec` with `mode="template"` and template
`contacts/ct_reply.html`.

`create_manual_message` has **no equivalent dispatch** — the function
returns immediately after the DB writes. The Compose form's "send"
button is wired to `ConversationsService.compose_message(request)`
(`cabinet/services/conversations.py:139`) which calls
`create_manual_message`; the chain ends in the database.

The `to_email` parameter is captured but only used as
`Message.sender_email`, which is inappropriate semantically — the
field was meant for the inbound message's sender, not the outbound
recipient.

## Fix — minimal, ships before any rename

### Step 1 — add `notify_compose_new` in `services/alerts.py`

Add at the top of the file (next to `notify_thread_reply`):

```python
def notify_compose_new(message, to_email: str) -> None:
    """Dispatch a freshly composed outbound email through the engine."""
    try:
        _get_notification_engine().dispatch_event(
            "conversations.compose_new", message, to_email
        )
    except Exception:
        log.exception(
            "Failed to dispatch compose-new notification for message_id=%s",
            message.pk,
        )
```

### Step 2 — register the event handler in `services/alerts.py`

```python
@notification_handler("conversations.compose_new")
def _build_compose_new_specs(message, to_email: str):
    return NotificationDispatchSpec(
        recipient_email=to_email,
        subject_key="conversations.compose_new.subject",
        subject=message.subject,
        event_type="conversations.compose_new",
        channels=["email"],
        mode="rendered",
        text_content=message.body,
        # No template_name — the worker delivers as plain text.
    )
```

`mode="rendered"` is correct for compose-new: the user-typed body is
the message; there is no template to render. If you want a layout
shell (header / footer / unsubscribe), render it Django-side and pass
`html_content` instead of `text_content`.

### Step 3 — wire the dispatch in `workflow.py:create_manual_message`

After line 41 (after `MessageReply.objects.create(...)`), add:

```python
    notify_compose_new(message, to_email)
    return message
```

And import at the top:

```python
from .alerts import notify_compose_new, notify_thread_reply
```

### Step 4 — fix the semantic abuse on `Message.sender_email`

This is a follow-up clean-up but should ride with the fix because
otherwise the audit trail is misleading.

The `Message` row created for compose-new has:
* `sender_name` = the staff user's full name
* `sender_email` = the recipient's email (wrong — this should be the
  staff user's outbound mailbox or `EmailSettings.email_from`)

Two options:

**Option A — quick fix:** add a `recipient_email` field to `Message`
and populate it from `to_email`. Leave `sender_email` blank for
manual messages.

**Option B — defer:** ship the dispatch fix now; capture the
`recipient_email` field in the upcoming `AbstractMessage` migration
(`docs/dev/messaging_migration/03_features_rename.md`).

Recommendation: **Option B.** The dispatch fix is urgent; the schema
clean-up rides with the rename. Document the wart in a
`# TODO(messaging-migration)` comment on the bug fix commit.

## After the rename

When `features/conversations/` becomes `features/messaging/`, this
fix carries forward unchanged — the event key becomes
`messaging.compose_new` and the handler decoration uses
`@email_rendered`:

```python
@email_rendered("messaging.compose_new", channels=["email"])
def build_compose_new(message, to_email: str):
    return {
        "recipient_email": to_email,
        "subject_key": "messaging.compose_new.subject",
        "subject": message.subject,
        "html_content": render_to_string(
            "emails/compose_new.html", {"message": message}
        ),
        "text_content": message.body,
    }
```

The migration code in Phase 5 swaps the `@notification_handler` to
`@email_rendered`. The behavior is identical; the decorator is just
more declarative.

## Tests to add (Phase 1, before the rename)

```python
# tests/features/conversations/test_compose_dispatch.py
@pytest.mark.django_db
def test_compose_new_dispatches_email(monkeypatch):
    captured = []
    monkeypatch.setattr(
        "features.conversations.services.alerts._get_notification_engine",
        lambda: FakeEngine(captured),
    )
    user = UserFactory()
    msg = create_manual_message(
        to_email="recipient@example.com",
        subject="Hi",
        body="Hello there",
        user=user,
    )
    assert msg.pk is not None
    assert len(captured) == 1
    spec = captured[0]
    assert spec.event_type == "conversations.compose_new"
    assert spec.recipient_email == "recipient@example.com"
    assert spec.subject == "Hi"
    assert spec.text_content == "Hello there"
    assert spec.mode == "rendered"
```

`FakeEngine` records `dispatch_spec` calls without enqueueing.

## Why this is Phase 1 (before the rename)

* The bug is shipping today; staff are quietly losing every
  compose-new email.
* The fix is < 30 lines of code and zero schema changes.
* Shipping it ahead of the rename gives:
  * Immediate user-visible value.
  * A working baseline to verify the rename does not regress.
  * The handler shape that the new `@email_rendered` decorator will
    later wrap — so the rename is cosmetic.

## Anti-patterns to avoid

* **Reusing `notify_thread_reply()` for compose-new.** Reply
  semantics include thread headers (`In-Reply-To`, `References`)
  pointing at an inbound message. Compose-new has no inbound peer;
  reusing the reply path produces malformed thread headers.
* **Sending via `django.core.mail.send_mail` from the cabinet view.**
  The cabinet view runs synchronously; `send_mail` would block the
  request and bypass the worker fallback chain (SMTP → SendGrid).
  Always go through the engine.
* **Adding the dispatch directly inside `ComposeView.post`.** Keeps
  the dispatch logic out of the service layer and makes testing
  harder. Service layer (`workflow.py`) is the right place.
