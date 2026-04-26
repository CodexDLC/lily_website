# Lily — Phased Rollout Plan

The migration ships across nine independent phases. Each phase keeps
the system green; rollback at any phase is a revert plus the
documented rollback recipe.

## Phase 0 — Documentation (this commit)

* Deliver this doc set + the codex-platform / codex-django doc sets.
* No code changes.
* No production impact.

**Done when**: every `.md` is reviewed and merged into `main`.

## Phase 1 — Compose-new email bug fix

Targets: ship a working compose-new path **before** any rename.

* Add `notify_compose_new` in
  `features/conversations/services/alerts.py`.
* Add `_build_compose_new_specs` handler.
* Wire the dispatch in
  `features/conversations/services/workflow.py:create_manual_message`.
* Tests: `test_compose_new_dispatches_email`,
  `test_compose_new_does_not_send_to_blank_email`.

**Done when**:

1. Cabinet → Compose → submit → recipient receives email.
2. `EmailLog` row appears (well, today there's no `EmailLog` — there
   will be after Phase 4. For Phase 1 verification, look at the worker
   logs for the dispatch.)
3. CI green; `test_compose_new_dispatches_email` passes.

**Rollback**: revert the commit. The Compose form returns to its
original (broken) state.

**No schema changes; safe to ship as a hotfix.**

## Phase 2 — Library: codex-platform rename

Library work, separate PR in codex-tools repo.

* Create `src/codex_platform/messaging/` mirroring `notifications/`.
* Add `ThreadHeadersDTO`, `CampaignBatchDTO`,
  `CampaignRecipientDraft`, `AudienceBuilder`, `CampaignDispatcher`,
  `messaging.threading.*` helpers.
* Replace old `notifications/__init__.py` etc. with deprecation
  shims.
* No lily changes; lily keeps importing `codex_platform.notifications`
  through the shim.

**Done when**:
1. `codex-platform` test suite green for both old and new imports.
2. CI lint: no `import django` inside `messaging/`.

**Rollback**: revert in codex-platform; lily is unchanged.

## Phase 3 — Library: codex-django messaging package + abstract models

Library work.

* Create `src/codex_django/messaging/` mirroring `notifications/`.
* Add abstract models (`AbstractEmailSettings`,
  `AbstractSystemRecipient`, `AbstractEmailLog`, `AbstractThread`,
  `AbstractMessage`, `AbstractMessageReply`, `AbstractCampaign`,
  `AbstractCampaignRecipient`).
* Add `BaseAudienceBuilder` Django concrete base.
* Add `EmailSettingsSyncMixin` + `EmailSettingsRedisManager`.
* Add `@email_template`, `@email_rendered` decorators.

**Done when**: codex-django test suite green for both old and new
imports; abstract models import without errors.

**Rollback**: revert in codex-django; lily unchanged.

## Phase 4 — Lily: extract `EmailSettings`

Lily-side. Depends on Phase 3.

* Create `features/messaging/messaging_settings.py:EmailSettings`.
* Migration A: create EmailSettings table + copy data from
  SiteSettings.
* Update consumers (booking notifications, cabinet view, admin).
* Worker reads from new Redis hash `email_settings:` (with fallback
  to legacy `site_settings:`).
* Migration B: remove email-identity + url_path_* + site_base_url +
  logo_url fields from SiteSettings.

**Done when**:

1. `python manage.py migrate` succeeds in both directions.
2. `EmailSettings.load()` returns the previously-stored values.
3. Booking + thread-reply emails still send and contain the correct
   site URL / logo URL.
4. Cabinet's existing site-settings page no longer shows the moved
   fields.
5. Worker reads `email_settings:` after restart; SMTP and SendGrid
   sends both succeed.

**Rollback**: revert migration B (fields restored on SiteSettings),
revert consumer updates. Migration A's EmailSettings table can stay;
the data is duplicated but harmless until Phase 4 re-ships.

## Phase 5 — Lily: rename `features/conversations` → `features/messaging`

Depends on Phases 3 + 4.

* Move files via `git mv`.
* Subclass abstract models (introduces split: Conversation +
  Message).
* Add migration 3a (add `Conversation` table + nullable FK on
  Message; backfill).
* Add import shims at `features/conversations/__init__.py` and
  `features/notifications/__init__.py` (with `DeprecationWarning`).
* Rename URL routes; add redirect routes for old URLs.
* Update `INSTALLED_APPS`.

**Done when**:

1. `python manage.py migrate` succeeds.
2. Existing message data is reachable via `Conversation.messages`.
3. Old URL `/cabinet/conversations/inbox/` redirects to
   `/cabinet/messaging/inbox/`.
4. CI green; deprecation-warning gate (treating warnings as errors)
   is documented but disabled — turn it on after Phase 8.

**Rollback**: revert; the migrations have a paired no-op `RunPython`
for backward direction.

## Phase 6 — Lily: messaging cabinet (mirror booking)

Depends on Phase 5.

* Add `cabinet/views/messaging.py` with `MessagingSettingsView`,
  `ComposeView`, `InboxView`, `CampaignsListView`, etc.
* Add `cabinet/urls/messaging.py`.
* Add `templates/cabinet/messaging/*.html`.
* Update `features/messaging/cabinet.py:declare()` with full sidebar.

**Done when**:

1. Visiting `/cabinet/messaging/settings/` renders the form with
   grouped sections.
2. Saving the form persists to `EmailSettings`.
3. Sidebar entries (Compose, Inbox, …, Campaigns, Settings) match
   the screenshot.
4. Compose form still dispatches correctly (Phase 1 fix carried).

**Rollback**: revert; cabinet falls back to the conversations URL
redirects from Phase 5.

## Phase 7 — Decorator surface + sender-name fix

Depends on Phase 5.

* Replace `@notification_handler` with `@email_template` /
  `@email_rendered` in `services/alerts.py` and any builder code.
* Worker: read `email_sender_name` from
  `WorkerEmailSettings.email_sender_name`; pass through to
  `AsyncEmailClient` and `SendGridChannel`.
* Remove the hardcoded `"LILY Beauty Salon"` literal.

**Done when**:

1. Sending through the SendGrid fallback emits the configured sender
   name (verified by capturing the SendGrid request payload).
2. Setting `email_sender_name` in cabinet immediately reflects in the
   next email send (Redis sync confirmed).

**Rollback**: revert; the `@notification_handler` style still works.

## Phase 8 — Cleanup

Depends on Phases 1–7 having shipped to production for at least one
sprint.

* Remove `codex_platform.notifications` shims.
* Remove `codex_django.notifications` shims.
* Remove `features.conversations` and `features.notifications` import
  shims.
* Remove old `X-Lily-Thread-Key` header (only `X-Codex-Thread-Key`
  emitted).
* Remove legacy URL redirects.
* Remove legacy Redis key `site_settings:` (writes only to the new
  one).

**Done when**: deprecation-warning-as-error CI gate is green; no code
in the project imports anything deprecated.

**Rollback**: re-add the shims (everything is a string-level mapping;
no schema changes).

## Risk × benefit per phase

| Phase | Risk | User-visible benefit |
|-------|------|---------------------|
| 0 | None | None (planning artifact) |
| 1 | Low | Compose works |
| 2 | Low | Library cleanup |
| 3 | Low | Library cleanup |
| 4 | **Medium** (DB migration, worker config) | Cleaner settings; cabinet ready for messaging UI |
| 5 | **Medium** (large rename, data migration) | Single feature surface for messaging |
| 6 | Low (UI only) | Dedicated messaging cabinet page |
| 7 | Low | Sender name correct; cleaner decorator API |
| 8 | Low | Less deprecated code in tree |

Phase 4 is the largest single step; review its migrations in PR
carefully and rehearse migration B's rollback once on staging before
production.

## Cadence

Suggested ship cadence (assuming a one-week sprint):

| Sprint | Ship |
|--------|------|
| W1 | Phase 0 (docs) + Phase 1 (compose fix as hotfix) |
| W2 | Phase 2 + Phase 3 (library work in codex-tools) |
| W3 | Phase 4 (settings extraction; medium-risk; deserves a sprint) |
| W4 | Phase 5 (rename) |
| W5 | Phase 6 (cabinet) + Phase 7 (decorators + sender name) |
| W7 | Phase 8 (cleanup, after a soak period) |

Phase 8 is intentionally a sprint after Phase 7 — let production run
for at least 5 business days with the deprecation warnings active so
any straggler import is caught.
