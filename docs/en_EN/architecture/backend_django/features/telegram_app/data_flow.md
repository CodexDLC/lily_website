# 📄 Data Flow

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

This document outlines the asynchronous data flow from the moment an admin submits a reply in the TMA to the final UI update in the Telegram channel.

## 🔄 The Cycle

The `telegram_app` heavily relies on decoupled systems to ensure reliability and performance. We use **Django** for handling the incoming web request, **ARQ** (Redis queue) for background processing, and **Redis Streams** for event-driven communication back to the Bot.

### Step-by-Step Execution

1.  **Form Submission (TMA -> Django):**
    *   Admin clicks "Send".
    *   TMA sends a POST request with the reply text, `request_id`, and `initData` to a Django endpoint.
    *   Django validates the security tokens.

2.  **Queuing the Task (Django -> ARQ):**
    *   Instead of sending the email synchronously, Django enqueues a task: `await arq.enqueue_job('send_reply_email', request_id, reply_text)`.
    *   Django immediately responds with `200 OK` to the TMA. TMA closes.

3.  **Processing the Email (ARQ Worker):**
    *   The ARQ worker picks up the job.
    *   It fetches the client's email address from the database using `request_id`.
    *   It sends the actual email via SMTP/API.

4.  **Publishing the Event (ARQ Worker -> Redis Stream):**
    *   Upon successful email delivery (or failure), the ARQ worker publishes an event to a Redis Stream, e.g., `notification_status`.
    *   Payload example: `{"request_id": 123, "status": "success", "action": "reply_sent"}`.

5.  **Bot UI Update (Redis Stream -> Bot -> Telegram):**
    *   The Telegram Bot process (or a separate listener orchestrated by `NotificationsOrchestrator`) is continuously pulling from the `notification_status` stream.
    *   It receives the event.
    *   It calls `edit_message_text` or `edit_message_reply_markup` on the original channel message.
    *   The inline button "✍️ Reply" is removed, and the text is updated to prefix ✅ *Replied*.
    *   If the event was an `error`, the message text is updated to reflect the failure (❌ *Email failed*), but the button might be preserved for a retry.
