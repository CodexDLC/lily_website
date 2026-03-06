# 📬 Notifications Module

[⬅️ Back to Docs Root](../../README.md)

The `notifications` subsystem is designed to completely isolate the business logic of creating emails and messages from the transport layer of sending them. It handles formatting and building outbound messages (Emails, SMS, Telegram) in a framework-agnostic way.

## 🏗️ Architectural Concept

Historically, sending emails in Django is hardcoded deep into services, making the code slow and hard to test (synchronous `send_mail` calls).

In `codex_tools`:
1. **The Core only formats the payload (Builder)**. Instead of rendering HTML or connecting to SMTP, `NotificationPayloadBuilder` simply creates a standardized dictionary (JSON) with variables (`context_data`) and a list of required channels (`channels`).
2. **The Core passes the payload to an Adapter**. The built-in `BaseNotificationEngine` takes the ready dictionary and tells the Adapter: "Put this in the queue."
3. **Sending happens externally**. On the infrastructure side, a separate worker (ARQ or Celery) takes this JSON, finds the HTML template by `template_name`, renders it, and sends it via an external API (Postmark, Twilio, Telegram).

This ensures perfect Separation of Concerns.

## 🗂️ Module Map

### `NotificationPayloadBuilder` (`builder.py`)
Centralizes the creation of the payload dictionary. It guarantees that any dispatched task will have correctly formatted keys like:
- `notification_id`
- `recipient` (email, phone, first_name)
- `template_name`
- `context_data` (for template rendering variables)
- `channels` (list of allowed dispatch channels, e.g. `['email', 'telegram']`)

### `BaseNotificationEngine` (`service.py`)
The orchestrator class. Modules using `codex_tools` should instantiate this (or subclass it) by passing an `adapter` that implements an `.enqueue(task_name, payload)` method.

### `Adapters` (`adapters/`)
Like the booking module, communication with the actual project framework happens through adapters. For example, `django_adapter.py` wraps around ARQ clients or Celery to push the dictionaries created by the `Builder` into the actual Redis queues.
