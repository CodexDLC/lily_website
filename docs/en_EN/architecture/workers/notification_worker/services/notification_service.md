# 📜 Notification Service

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

Central service for preparing and sending email notifications.

**File:** `src/workers/notification_worker/services/notification_service.py`

## `NotificationService` Class

### Constructor

Accepts SMTP credentials, SendGrid API key, site URL, logo URL, and URL path templates for action links (confirm, cancel, reschedule, contact form).

Creates internally:
- `AsyncEmailClient` — for SMTP sending
- `TemplateRenderer` — for Jinja2 HTML rendering

### Key Methods

#### `send_notification(email, subject, template_name, data)`

Main entry point:
1. Calls `enrich_email_context(data)` to build full template context.
2. Renders HTML via `self.renderer.render(template_name, context)`.
3. Sends via `self.email_client.send_email(email, subject, html)`.

#### `enrich_email_context(data) -> dict`

Enriches raw appointment data with:
- Parsed `date` and `time` from datetime string
- `site_url`, `logo_url`
- Action links: `link_confirm`, `link_cancel`, `link_reschedule`, `contact_form_url`
- Google Calendar URL
- Visit-count-based greeting (formal → informal)

#### `get_sms_text(data) -> str`

Generates a plain-text SMS confirmation message in German, with transliterated name.

#### `get_absolute_logo_url() -> str | None`

Resolves the logo URL to an absolute path. Falls back to a default static path.
