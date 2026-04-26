# Lily Messaging Migration — Summary

## Why this exists

Lily today carries four interleaved concerns under
`features/conversations/` + `features/notifications/` + the
`notification_worker`: outbound notifications, inbound mail import,
threaded conversations, and mass-email campaigns. The user wants:

1. A single, cleanly layered `codex-messaging` library shared with
   future projects.
2. A focused `EmailSettings` model + cabinet page (like booking has),
   instead of email config buried inside `SiteSettings`.
3. A working compose-new email path (currently broken at
   `features/conversations/services/workflow.py:18-42`).
4. Two decorator styles for project-side email content builders
   (template + rendered modes) as called for in conversations.

The library work happens in `codex-platform` and `codex-django` (see
their `docs/dev/messaging/` directories). This doc set covers the
**lily-side** migration: rename, settings extraction, compose-new
fix, worker alignment, and verification.

## Current state

| Concern | Module | Status |
|---------|--------|--------|
| Outbound notifications via codex_django.notifications | `features/conversations/services/notifications.py` | Working. |
| Admin alerts (new contact, thread reply) | `features/conversations/services/alerts.py` | Working. |
| Mass-email campaigns | `features/conversations/services/campaign_service.py`, `campaigns/`, `selector/audience.py`, worker `tasks/campaign_tasks.py` | Working. |
| Compose-new email from cabinet inbox | `features/conversations/services/workflow.py:18-42` (`create_manual_message`) | **Broken** — DB rows created, no dispatch. |
| Inbound email import | `services/email_import.py`, `services/threads.py`, `services/workflow.py` | Working. |
| Email-identity settings | `system/models/settings.py:SiteSettings` via `SiteEmailIdentityMixin` | Working but bloated. |
| Worker SMTP/SendGrid send | `src/workers/notification_worker/services/notification_service.py`, `core/base_module/email_client.py` | Working. SendGrid hardcodes sender name `"LILY Beauty Salon"`. |
| Worker site-settings sync | `src/workers/core/site_settings.py` (Redis hash + env merge) | Working. |
| Cabinet — conversations | hand-rolled in `cabinet/views/conversations.py`, `cabinet/services/conversations.py` | Working. |
| Cabinet — settings page | sits inside system/site-settings auto-discovery | Mixed with non-messaging settings. |

## Target state

| Concern | Module | Status |
|---------|--------|--------|
| Outbound + alerts + compose | `features/messaging/services/` (rename + restructure) | All working through `BaseMessagingEngine`. |
| Models | `features/messaging/models/` subclassing abstract bases in `codex_django.messaging.mixins` | Concrete project models, library schema. |
| Email settings | `features/messaging/messaging_settings.py:EmailSettings` (singleton, mirrors `BookingSettings`) | Standalone model, own migrations, Redis sync via mixin. |
| Cabinet | `features/messaging/cabinet.py` + `cabinet/views/messaging.py` + `cabinet/urls/messaging.py` | Mirrors booking exactly. |
| Worker | `notification_worker` keeps its shape, internal renames only (read `email_settings:` Redis hash). | Working with new schema. |
| Compose-new | `services/compose.py` + `@email_rendered("messaging.compose_new")` builder | **Fixed** — dispatches via engine. |

## Five concrete code-level changes

The library work is mostly mechanical. The lily project carries five
non-mechanical changes that drive the verification plan:

1. **Compose-new bug fix** — `workflow.py:18-42` calls a new
   `notify_compose_new(message, to_email)`; new
   `@email_rendered("messaging.compose_new")` builder dispatches. See
   [`01_compose_new_email_fix.md`](01_compose_new_email_fix.md).

2. **Settings extraction** — move `email_from`, `email_sender_name`,
   `email_reply_to`, `site_base_url`, `logo_url`, `url_path_*` out of
   `SiteSettings` into `EmailSettings`. See
   [`02_settings_extraction.md`](02_settings_extraction.md).

3. **Features rename** — `features/conversations/` +
   `features/notifications/` → `features/messaging/` with import shims
   during deprecation. See
   [`03_features_rename.md`](03_features_rename.md).

4. **Worker alignment** — Redis key rename `site_settings:` →
   `email_settings:`; SendGrid sender name plumbing; payload
   `schema_version=1`. See
   [`04_workers_alignment.md`](04_workers_alignment.md).

5. **Phased rollout & verification** — see
   [`05_phase_plan.md`](05_phase_plan.md) and
   [`06_verification.md`](06_verification.md).

## Things explicitly NOT in scope

* Inbound email transport redesign. The current SendGrid Inbound Parse
  / IMAP path stays.
* Booking, system, cabinet refactors outside the messaging touchpoints.
* New SMS / WhatsApp / push channels (the abstract is ready for them
  but no concrete channel is being added now).
* Migrating SMTP credentials into the database (deliberately rejected
  — secrets stay in env, see comment in
  `core/settings/modules/email.py:1`).

## Reading order

1. [`05_phase_plan.md`](05_phase_plan.md) — phase-by-phase rollout
   (read first to get the shape of the work).
2. [`01_compose_new_email_fix.md`](01_compose_new_email_fix.md) — the
   bug that ships in Phase 1, before any rename.
3. [`02_settings_extraction.md`](02_settings_extraction.md) — Phase 4.
4. [`03_features_rename.md`](03_features_rename.md) — Phase 5.
5. [`04_workers_alignment.md`](04_workers_alignment.md) — Phase 4 + 7.
6. [`06_verification.md`](06_verification.md) — smoke tests per
   phase.

## Library docs cross-references

* `codex-platform/docs/dev/messaging/00_overview.md` for the
  framework-agnostic core.
* `codex-django/docs/dev/messaging/00_overview.md` for the Django
  adapter layer.
* `codex-django/docs/dev/messaging/04_cabinet_integration.md` for the
  booking-mirror cabinet pattern.
* `codex-django/docs/dev/messaging/05_settings_migration.md` for the
  abstract recipe (this lily doc applies it).
