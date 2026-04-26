# Lily — Renaming `features/conversations` + `features/notifications` → `features/messaging`

## Why rename

The two features today represent overlapping concerns: `notifications`
holds `NotificationLog` + `NotificationRecipient` (audit and admin
recipient registry); `conversations` holds threads, messages,
campaigns, and the entire dispatch service layer. Splitting along
those lines was historical — every piece is part of the same
"messaging" surface, and lifting them into one app makes the
boundary with the library cleaner.

## Target layout

```
src/lily_backend/features/messaging/
├── __init__.py
├── apps.py                              # MessagingConfig
├── messaging_settings.py                # EmailSettings (from doc 02)
├── cabinet.py                            # declare(module="messaging", …)
├── translation.py                        # registers translatable fields
├── persistence.py
├── models/
│   ├── __init__.py
│   ├── email_settings.py                 # re-export
│   ├── system_recipient.py               # NotificationRecipient(AbstractSystemRecipient)
│   ├── email_log.py                      # EmailLog(AbstractEmailLog)
│   ├── thread.py                         # Conversation(AbstractThread)
│   ├── message.py                        # Message(AbstractMessage)
│   ├── reply.py                          # MessageReply(AbstractMessageReply)
│   └── campaign.py                       # Campaign + CampaignRecipient
├── services/
│   ├── __init__.py
│   ├── alerts.py                         # @notification_handler / @email_template / @email_rendered builders
│   ├── compose.py                        # compose-new flow (the bug-fixed one)
│   ├── email_import.py                   # inbound parser (kept)
│   ├── notifications.py                  # legacy thin wrappers (deprecated)
│   ├── threads.py                         # state-transition helpers
│   ├── workflow.py                        # create_manual_message + create_reply
│   └── campaign_service.py
├── selector/
│   └── audience.py                        # LilyAudienceBuilder(BaseAudienceBuilder)
├── dispatcher.py                          # LilyArqCampaignDispatcher
├── builders/                              # @email_template / @email_rendered builders
│   └── __init__.py
└── api/
    ├── __init__.py
    └── campaigns.py                       # POST /messaging/campaigns/recipient-status
```

## Migration steps

### Step 1 — copy the files

Use `git mv` (preserves history) for every file:

```
git mv features/conversations/models      features/messaging/models
git mv features/conversations/services    features/messaging/services
git mv features/conversations/selector    features/messaging/selector
git mv features/conversations/api         features/messaging/api
git mv features/conversations/campaigns/* features/messaging/services/  # campaigns module folds in
git mv features/notifications/models/log.py      features/messaging/models/email_log.py
git mv features/notifications/models/recipient.py features/messaging/models/system_recipient.py
```

### Step 2 — switch to abstract bases

Each model file changes its base class:

```python
# Before
from django.db import models

class Message(models.Model):
    ...

# After
from codex_django.messaging.mixins import AbstractMessage

class Message(AbstractMessage):
    # only the lily-specific fields remain:
    topic        = models.CharField(...)
    is_read      = models.BooleanField(...)
    is_archived  = models.BooleanField(...)
    dsgvo_consent  = models.BooleanField(...)
    consent_marketing = models.BooleanField(...)
    lang         = models.CharField(...)
    admin_notes  = models.TextField(...)
```

Compare to `BookingSettings(AbstractBookingSettings)` in
`features/booking/booking_settings.py:15` — same shape.

### Step 3 — split `Message` into `Conversation + Message`

The lily `Message` model today carries both thread-root identity
(`thread_key`, `subject`, `sender_*`) and per-message content (`body`,
`is_read`, `is_archived`). The migration introduces `Conversation`
(thread root) and `Message` (a single message in the thread).

Data migration:

```python
def split_thread_from_message(apps, schema_editor):
    OldMessage = apps.get_model("messaging", "Message")
    Conversation = apps.get_model("messaging", "Conversation")
    NewMessage = apps.get_model("messaging", "Message")  # same class, after FK added

    seen_threads: dict[str, int] = {}
    for old in OldMessage.objects.all():
        if old.thread_key not in seen_threads:
            conv = Conversation.objects.create(
                thread_key=old.thread_key,
                subject=old.subject,
                status=old.status,
            )
            seen_threads[old.thread_key] = conv.pk
        # link old.thread = conv via FK update
        OldMessage.objects.filter(pk=old.pk).update(
            thread_id=seen_threads[old.thread_key]
        )
```

Two-phase:

* **Phase 3a**: add `thread` FK (nullable) and `Conversation` table;
  RunPython populates them.
* **Phase 3b** (later release): make `thread` non-null, drop
  `thread_key` from `Message`.

This staged migration keeps prod fully online during the rollover.

### Step 4 — import shims

To keep external consumers (other modules in the project, tests,
admin scripts) working, add temporary import shims:

```python
# features/conversations/__init__.py
"""DEPRECATED: use features.messaging instead."""
import warnings

warnings.warn(
    "features.conversations is deprecated; use features.messaging",
    DeprecationWarning,
    stacklevel=2,
)

from features.messaging.models import (  # noqa: F401
    Message,
    MessageReply,
    Conversation,
    Campaign,
    CampaignRecipient,
)
from features.messaging.services import (  # noqa: F401
    notify_thread_reply,
    notify_compose_new,
    create_manual_message,
    create_reply,
)
```

Same shape for `features/notifications/__init__.py`.

The shims emit one `DeprecationWarning` per import. In CI, treat
deprecation warnings as errors only on the messaging branch — break
import paths that should already be migrated.

### Step 5 — URL routes

The cabinet routes in `cabinet/urls/conversations.py` move to
`cabinet/urls/messaging.py`. The route names change from
`cabinet:conversations_*` to `cabinet:messaging_*`. Add backward-
compatible URL redirects for one minor release:

```python
# cabinet/urls/__init__.py
from django.views.generic import RedirectView

urlpatterns = [
    # …
    path("conversations/", RedirectView.as_view(pattern_name="cabinet:messaging_inbox", permanent=False)),
    path("conversations/<path:rest>", RedirectView.as_view(url="/cabinet/messaging/%(rest)s", permanent=False)),
]
```

Bookmarked links keep working until users update them.

### Step 6 — `INSTALLED_APPS`

* Remove `features.conversations`.
* Remove `features.notifications`.
* Add `features.messaging`.

If `apps.py` in either old feature has signal handlers, port them to
`features/messaging/apps.py:MessagingConfig.ready()`.

### Step 7 — admin

`system/admin/settings.py` no longer registers the email-identity
fields (those moved to `EmailSettings` admin). `MessagingAdmin`
classes register `Conversation`, `Message`, `MessageReply`,
`Campaign`, `CampaignRecipient`, `EmailLog`, `NotificationRecipient`,
`EmailSettings`.

### Step 8 — translations

If `translation.py` registered `Message`/`Campaign` for
django-modeltranslation, port the registration to
`features/messaging/translation.py`. Re-run
`python manage.py update_translation_fields` after the migration.

### Step 9 — handler decorators (optional, follows Phase 7)

Once codex-django ships `@email_template` / `@email_rendered`,
rewrite the handlers in `services/alerts.py`:

```python
# Before
@notification_handler("conversations.thread_reply")
def _build_thread_reply_specs(message, reply):
    return NotificationDispatchSpec(...)

# After
@email_template("messaging.thread_reply", channels=["email"])
def build_thread_reply(message, reply):
    return {
        "recipient_email": message.sender_email,
        "subject_key": "messaging.thread_reply.subject",
        "subject": _build_reply_subject(message),
        "template_name": "contacts/ct_reply.html",
        "context": _build_reply_context(message, reply),
    }
```

Behavior is identical; the decorator is more declarative.

## Rename targets table

| Old | New |
|-----|-----|
| `features/conversations` | `features/messaging` |
| `features/notifications` | (folded into `features/messaging`) |
| `features/conversations/services/notifications.py` | `features/messaging/services/notifications.py` (deprecated wrapper) |
| `features/conversations/services/alerts.py` | `features/messaging/services/alerts.py` |
| `features/conversations/campaigns/` | `features/messaging/services/` (folded) |
| `features/conversations/selector/audience.py` | `features/messaging/selector/audience.py` |
| `features/conversations/api/campaigns.py` | `features/messaging/api/campaigns.py` |
| `features/notifications/models/log.py:NotificationLog` | `features/messaging/models/email_log.py:EmailLog` |
| `features/notifications/models/recipient.py:NotificationRecipient` | `features/messaging/models/system_recipient.py:NotificationRecipient` |
| `cabinet/urls/conversations.py` | `cabinet/urls/messaging.py` |
| `cabinet/views/conversations.py` | `cabinet/views/messaging.py` |
| `cabinet/services/conversations.py` | `cabinet/services/messaging.py` |
| `cabinet:conversations_*` URL names | `cabinet:messaging_*` |
| Event key `conversations.new_message` | `messaging.new_message` |
| Event key `conversations.thread_reply` | `messaging.thread_reply` |
| Event key `conversations.compose_new` | `messaging.compose_new` |

## Risk summary

| Risk | Mitigation |
|------|-----------|
| Imports broken in tests | Import shims with `DeprecationWarning` |
| Old URLs in user bookmarks | URL redirects for one minor release |
| Admin links 404 | Redirects + `system/admin/settings.py` cleanup |
| Pending ARQ jobs in the queue under old payload format | `payload_dict` is mode-tolerant; no schema break |
| Modeltranslation migration loss | Re-run `update_translation_fields` after migration |
| Old event keys in the registry | Register both keys during deprecation window |

## Anti-patterns

* **Renaming files without `git mv`.** Loses history; future
  `git blame` becomes painful.
* **Big-bang migration in one PR.** The phased plan
  (`docs/dev/messaging_migration/05_phase_plan.md`) splits this rename
  across multiple PRs so each phase can ship independently.
* **Skipping the import shims.** Tests in unrelated apps may import
  `features.conversations.models.Message`; without shims, those break.
* **Deleting old event keys before checking the registry.** During
  the deprecation window, both old and new keys MUST be registered;
  consumers are migrated incrementally.
