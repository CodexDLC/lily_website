# Lily — Worker Alignment with `codex-messaging`

## What changes for the worker

The `notification_worker` is already framework-agnostic and reads
config from env vars + Redis hash. The migration touches:

1. **Redis hash key rename**: `site_settings:` → `email_settings:`.
2. **`WorkerSiteSettings` Pydantic model rename**: → `WorkerEmailSettings`.
3. **SendGrid sender name plumbing**: read from `email_sender_name`
   instead of the hardcoded literal `"LILY Beauty Salon"` at
   `core/base_module/email_client.py:113`.
4. **Payload `schema_version=1`**: workers MAY reject payloads with a
   higher schema version (forward-compat).
5. **Promotion of `_mailbox_headers()` into platform helpers** (only a
   refactor — the lily worker keeps its current call shape).
6. **Worker callbacks for single notifications** (terminal status):
   the existing campaign callback shape becomes the standard for all
   notifications.

No worker code path's behavior changes for the user — these are
internal renames + one bug fix (sender name).

## Files touched

| File | Change |
|------|--------|
| `src/workers/core/site_settings.py:1-80` | Rename class `WorkerSiteSettings` → `WorkerEmailSettings`. Rename function `merge_email_settings` keeps its name. Read from new Redis key `email_settings:` with fallback to `site_settings:` during deprecation. |
| `src/workers/notification_worker/dependencies.py:43-59` | Inject `WorkerEmailSettings` into `NotificationService` (rename only). Add `email_sender_name` to the kwargs passed in. |
| `src/workers/notification_worker/services/notification_service.py` | Accept `email_sender_name` constructor arg. Pass it through to `AsyncEmailClient` and the SendGrid path. |
| `src/workers/core/base_module/email_client.py:103-129` | Read sender name from `self.email_sender_name`; default to `from_email.split("@")[0]` if empty; never hardcode. |
| `src/workers/notification_worker/tasks/notification_tasks.py` | Add `schema_version` validation at the top of `send_universal_notification_task`. Add terminal-status callback to `/messaging/notifications/status` on final success/failure. |
| `src/workers/notification_worker/tasks/campaign_tasks.py` | Update callback URL from `/campaigns/recipient-status` to `/messaging/campaigns/recipient-status` (with a fallback to old URL during deprecation). |

## Rename: `site_settings:` → `email_settings:`

### Reader (worker)

```python
# src/workers/core/site_settings.py (after migration)
EMAIL_SETTINGS_HASH_KEY  = "email_settings:"
LEGACY_HASH_KEY          = "site_settings:"   # remove after deprecation


class SiteSettingsRedisReader:
    async def load(self, redis) -> WorkerEmailSettings:
        # Prefer new key
        data = await redis.hgetall(EMAIL_SETTINGS_HASH_KEY)
        if not data:
            data = await redis.hgetall(LEGACY_HASH_KEY)
        return WorkerEmailSettings.model_validate(_decode(data)) if data else WorkerEmailSettings()
```

### Writer (Django)

The Django side adds `EmailSettingsRedisManager` (lives in
`codex_django.messaging.adapters`, see
`codex-django/docs/dev/messaging/05_settings_migration.md`). It hooks
the `post_save` signal of `EmailSettings` and writes to
`email_settings:`.

During the deprecation window, the **legacy** writer
(`DjangoSiteSettingsManager` in codex-django) keeps writing
`site_settings:` for the fields that haven't moved yet. This
double-write window ends when migration B (the field-removal one)
ships.

### Verification

1. `redis-cli HGETALL email_settings:` returns the email identity
   fields after a save in Django admin.
2. `redis-cli HGETALL site_settings:` no longer returns the email
   fields after migration B ships.
3. Worker boots cleanly with the new key.

## Sender name fix

Today, `email_client.py:113`:

```python
def _payload_for_sendgrid(...):
    return {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": "LILY Beauty Salon"},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_content}],
    }
```

After migration, `AsyncEmailClient` (and the new `SendGridChannel`)
accept `from_name` via constructor:

```python
class AsyncEmailClient:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        smtp_from_email: str | None = None,
        smtp_from_name: str | None = None,   # new
        smtp_use_tls: bool = False,
    ) -> None:
        self.smtp_from_name = smtp_from_name or (smtp_from_email or "").split("@")[0]
        ...
```

`SendGridChannel` uses the same value:

```python
"from": {"email": self.from_email, "name": self.from_name},
```

The `dependencies.py` factory reads
`worker_email_settings.email_sender_name` from the merged config and
passes it to both clients.

### Verification

* In `EmailSettings` admin (cabinet), set `email_sender_name` to
  `"Lily Beauty Studio"`.
* Trigger a send (e.g. test booking confirmation).
* Inspect the SMTP log + SendGrid dashboard — both show
  `Lily Beauty Studio` as the From display name.
* Force SMTP to fail (block port 587) — SendGrid fallback engages and
  uses the same sender name.

## `schema_version`

Add to every payload:

```python
{
    "schema_version": 1,
    "mode": "template",
    "notification_id": ...,
    ...
}
```

Worker check:

```python
async def send_universal_notification_task(ctx, payload_dict):
    schema_version = payload_dict.get("schema_version", 1)
    if schema_version > MAX_SUPPORTED_SCHEMA_VERSION:
        log.error("Worker schema_version too low: %s > %s", schema_version, MAX_SUPPORTED_SCHEMA_VERSION)
        return
    ...
```

This costs nothing at v1 but lets future migrations add fields without
worker breakage when payloads roll forward.

## Terminal-status callback (new)

Today, only campaign jobs call back to Django (`/campaigns/recipient-status`).
Booking and admin-alert sends silently succeed; there's no audit row.

After migration, every send calls back on terminal status:

* On final success: `POST /messaging/notifications/status` with
  `{notification_id, status: "sent", provider_message_id}`.
* On final failure (after retries exhausted): same URL with
  `status: "failed"`, `error: "<reason>"`.

The Django endpoint upserts an `EmailLog` row keyed by
`notification_id`. Hosts wire the URL via the `callback_url` field on
the payload — the worker does not hardcode the URL.

### Implementation sketch

```python
# tasks/notification_tasks.py
async def _report_terminal_status(payload, status, error=""):
    callback_url = payload.get("callback_url")
    if not callback_url:
        return  # backwards-compat: legacy payloads have no URL
    async with httpx.AsyncClient() as client:
        await client.post(
            callback_url,
            json={
                "notification_id": payload["notification_id"],
                "status": status,
                "error": error,
                "provider_message_id": payload.get("provider_message_id", ""),
            },
            headers={"Authorization": f"Bearer {payload['callback_token']}"},
            timeout=15,
        )
```

The Django endpoint validates the bearer token via the existing
`OPS_WORKER_API_KEY` mechanism (`system/api/auth.py:12-18`).

## Promotion of `_mailbox_headers()` into platform helpers

Today:

```python
# tasks/notification_tasks.py:103-113
def _mailbox_headers(thread_key: str | None, message_id: str | None, references: str | None):
    headers = {}
    if message_id:
        headers["Message-ID"] = message_id
    if references:
        headers["References"] = references
        headers["In-Reply-To"] = references.split()[-1]
    if thread_key:
        headers["X-Lily-Thread-Key"] = thread_key
    return headers
```

After migration, this lives in
`codex_platform.messaging.threading.render_email_headers(dto)` and
emits both `X-Lily-Thread-Key` and `X-Codex-Thread-Key` (the new
neutral name) during deprecation. The lily worker imports the helper
instead of defining its own.

After deprecation, `X-Lily-Thread-Key` is removed; only
`X-Codex-Thread-Key` remains.

## Backward compatibility window

| Surface | Old | New | Window |
|---------|-----|-----|--------|
| Redis hash key | `site_settings:` | `email_settings:` | One minor release of double-writes. |
| Worker class name | `WorkerSiteSettings` | `WorkerEmailSettings` | Old name aliased for one release. |
| Email header | `X-Lily-Thread-Key` | `X-Codex-Thread-Key` | Both emitted during deprecation. |
| Campaign callback URL | `/campaigns/recipient-status` | `/messaging/campaigns/recipient-status` | Old URL aliased; worker tries new first. |
| Hardcoded sender | `"LILY Beauty Salon"` | from `email_sender_name` | No backward compat — fix is correct, old behavior was a bug. |

## Anti-patterns

* **Skipping the double-write window for Redis.** A single-step
  rename causes a window where the worker boots with empty config
  while Django still writes the old key.
* **Removing the deprecation aliases before downstream consumers
  migrate.** Old payloads in the queue reference old task names; old
  bookmarks reference old URLs. The aliases give time for everything
  to roll.
* **Adding `provider_message_id` to the `Message` model.** It belongs
  on `EmailLog`, not on `Message`. The model owns audit; the
  conversation owns content.
