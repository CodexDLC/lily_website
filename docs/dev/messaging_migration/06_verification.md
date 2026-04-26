# Lily — Verification Plan

For each phase, this document lists the smoke tests, automated tests,
and manual checks that prove the phase is shippable. Treat each
checklist as a release-gate.

## Phase 1 — Compose-new fix

### Automated

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

### Manual (staging)

1. Log in as staff; visit `/cabinet/conversations/compose/`.
2. Fill: To = your inbox, Subject = "Compose-new fix test",
   Message = "If you see this, the fix works.".
3. Click "Отправить".
4. Within 30 seconds, verify the email arrives at your inbox.
5. Verify the From displayed in the email matches
   `EmailSettings.email_sender_name` (after Phase 4) or the current
   `SiteSettings.email_sender_name` (Phase 1 only).

### Production smoke

After deploy, monitor the worker logs for:

* `"AsyncEmailClient | sent to='..."` for the event_type
  `conversations.compose_new`.
* No `"Failed to dispatch compose-new notification"` errors.

## Phase 2 — codex-platform rename

### Automated

* `pytest tests/notifications/` — old import path still works.
* `pytest tests/messaging/` — new import path works.
* `pytest --strict-warnings` — no new deprecation warnings outside
  the deprecation shims themselves.

### Manual

* `python -c "from codex_platform.notifications import NotificationPayloadDTO; print(NotificationPayloadDTO)"`
  prints the class without error.
* `python -c "from codex_platform.messaging import NotificationPayloadDTO; print(NotificationPayloadDTO)"`
  prints the same class.

## Phase 3 — codex-django messaging library

### Automated

* `pytest tests/notifications/` — old path still works.
* `pytest tests/messaging/` — new path works.
* New abstract models import cleanly: e.g.
  `from codex_django.messaging.mixins import AbstractEmailSettings`.
* Decorator round-trip:
  ```python
  @email_template("test.event", channels=["email"])
  def builder():
      return {"recipient_email": "x", "subject_key": "x", "template_name": "x.html"}

  specs = engine.dispatch_event("test.event")
  assert len(specs) == 1
  assert specs[0].mode == "template"
  ```

### Manual

* In a fresh Django project, scaffold `EmailSettings` from
  `AbstractEmailSettings`; `manage.py makemigrations` + `migrate`
  succeeds.

## Phase 4 — EmailSettings extraction

### Automated

```python
# tests/features/messaging/test_settings_migration.py
@pytest.mark.django_db(transaction=True)
def test_email_settings_extraction(transactional_db):
    # Pre-migration: data in SiteSettings
    site = SiteSettings.load()
    site.email_from = "test@example.com"
    site.email_sender_name = "Test Sender"
    site.site_base_url = "https://test.example.com"
    site.save()

    # Run migration A
    call_command("migrate", "messaging", "0001_initial")

    # Verify data copied
    es = EmailSettings.load()
    assert es.email_from == "test@example.com"
    assert es.email_sender_name == "Test Sender"
    assert es.site_base_url == "https://test.example.com"
```

```python
# tests/workers/test_redis_settings_sync.py
@pytest.mark.django_db
async def test_email_settings_redis_sync(redis_client):
    es = EmailSettings.load()
    es.email_sender_name = "New Name"
    es.save()

    data = await redis_client.hgetall("email_settings:")
    assert data[b"email_sender_name"] == b"New Name"
```

### Manual (staging)

1. Backup the database.
2. Apply migration A. Verify `EmailSettings.objects.count() == 1` and
   the row has the expected values.
3. Apply migration B. Verify the columns are gone from `SiteSettings`.
4. Trigger a booking confirmation. Verify the email contains the
   correct site URL and logo URL.
5. Trigger a thread-reply. Same check.
6. Inspect the SMTP log — verify From displays
   `email_sender_name`.
7. Block port 587 on the worker host. Trigger another send. Verify
   SendGrid fallback engages and uses the correct sender name (this
   tests the Phase 7 fix's prerequisite).

### Rollback rehearsal

On staging, before promoting:

1. Run migration B forward.
2. Run migration B backward (`migrate system 00XX-1`).
3. Verify `SiteSettings.email_from` etc. are restored to their
   pre-migration values **from the database backup** (the migration
   itself does not re-copy; rollback requires the backup).

## Phase 5 — Features rename

### Automated

* `pytest -W error::DeprecationWarning -p no:cacheprovider tests/`
  — no deprecation warnings except the one set we expect (the import
  shims).
* `pytest tests/features/messaging/` — passes (the renamed module).
* `pytest tests/features/conversations/` — passes (the import shim
  module emits one warning per import; tests still run).
* Reverse-FK access works:
  `conversation.messages.all()`, `message.replies.all()`,
  `campaign.recipients.all()`.

### Manual

1. Visit `/cabinet/conversations/` — get redirected to
   `/cabinet/messaging/`.
2. Visit a deep link from a saved bookmark
   (`/cabinet/conversations/thread/<id>/`) — get redirected to the
   equivalent messaging URL with the message preserved.
3. Inbox page shows existing threads (data was migrated, not lost).

## Phase 6 — Messaging cabinet

### Automated

* `test_messaging_settings_view_renders_form` — GET
  `/cabinet/messaging/settings/` returns 200 and the form has the
  expected sections.
* `test_messaging_settings_view_saves` — POST with new values
  persists to `EmailSettings.load()` and triggers the Redis sync.
* `test_compose_view_dispatches_through_engine` — POST to compose
  endpoint enqueues a job (verified via fake adapter).

### Manual

1. Take a screenshot of the messaging cabinet sidebar; verify it
   matches the user's expected layout (Compose, Inbox, Imported,
   Processed, All, Campaigns, New Campaign, Recipients, Settings).
2. Open the Settings tab; verify fields are grouped (Identity,
   Branding, Transactional Paths).
3. Change a field; save; reload — value persists.
4. Test all sidebar entries — each renders.

## Phase 7 — Decorators + sender-name fix

### Automated

* Existing `@notification_handler` tests still pass.
* New `@email_template` / `@email_rendered` tests pass.
* Rule-validation tests:
  ```python
  with pytest.raises(TypeError):
      @email_template("x", channels=["email"])
      def bad():
          return {"html_content": "..."}  # forbidden in template mode
  ```

### Manual

1. Set `EmailSettings.email_sender_name = "Lily Beauty Studio"`.
2. Save → triggers Redis sync.
3. Wait < 5s for worker to pick up new config (or restart worker).
4. Trigger a booking confirmation send. Inspect SMTP "From" header —
   value is `"Lily Beauty Studio" <noreply@lily.de>`.
5. Block SMTP port. Trigger another send. SendGrid fallback engages.
   Inspect SendGrid dashboard — "From" name is
   `"Lily Beauty Studio"`, NOT the old hardcoded `"LILY Beauty Salon"`.

## Phase 8 — Cleanup

### Automated

* CI gate enables `pytest -W error::DeprecationWarning` — must be
  green (no internal imports of deprecated paths remain).
* `grep -rn "X-Lily-Thread-Key" src/` returns nothing.
* `grep -rn "site_settings:" src/` returns only documentation.
* `grep -rn "features.conversations\|features.notifications" src/`
  returns nothing.

### Manual

* Open an email in Gmail, view headers — `X-Codex-Thread-Key`
  present, `X-Lily-Thread-Key` absent.
* Visit any old URL like `/cabinet/conversations/inbox` — gets a
  404, NOT a redirect (the redirect is removed in this phase).

## End-to-end smoke (production after Phase 7)

A single test exercising every messaging path:

1. Visit cabinet → messaging → Compose → send to your test inbox.
   Receive email.
2. Reply to the email from your inbox. Wait for inbound import to
   pick it up. Verify it appears in the cabinet inbox as an
   inbound `Message` linked to the existing thread.
3. From the thread view, click Reply, type response, send. Verify
   the response arrives at your inbox.
4. Trigger a booking. Receive confirmation email.
5. Cancel the booking. Receive cancellation email.
6. Reschedule the booking. Receive reschedule email.
7. From cabinet → messaging → New Campaign, build a small campaign
   targeting yourself. Send. Receive the marketing email.
8. Block port 587 on the worker host. Trigger any send. Receive via
   SendGrid fallback.
9. Inspect `EmailLog` rows in admin — every above send produced a row
   with status `sent`.

If any step fails, the corresponding phase is the place to look.
