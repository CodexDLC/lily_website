# 📱 Telegram App Feature

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

This feature implements the integration of Telegram Mini Apps (TMA) for administrative tasks. It allows administrators to process requests directly within the Telegram interface without switching to a different application, improving UX and security.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📄 Architecture & Security](./architecture_and_security.md)** | HMAC signing, token generation, and Telegram validation logic |
| **[📄 Frontend (TMA)](./frontend_tma.md)** | Base templates, Telegram UI integration, and form handling |
| **[📄 Data Flow](./data_flow.md)** | Django to ARQ to Redis to Telegram Bot communication |

## 🛠️ Development Tasks

This section outlines the implementation plan for the `telegram_app` feature. We follow a strict security model and maintain native Telegram aesthetics where possible.

### 1. Backend Architecture (Django)
- [ ] **Routing:** Create a dedicated namespace (e.g., `/tma/`).
- [ ] **Security (HMAC Signing & WebApp Validation):**
  - Implement a service to generate unique signatures (tokens) for URLs based on `request_id` and the project's secret key.
  - Implement `Telegram.WebApp.initData` validation to ensure the page is opened exclusively inside Telegram and by the correct user.
  - Create the `@tma_secure_required` decorator to validate the signature and the `initData` before serving the page. Return 404 if invalid.

### 2. Base Interface (Frontend TMA)
- [ ] **Base Template:** Create `tma_base.html` that imports `https://telegram.org/js/telegram-web-app.js`.
- [ ] **Styling Integration:** Configure CSS variables to use the Telegram theme (e.g., `var(--tg-theme-bg-color)`, `var(--tg-theme-button-color)`) so the app adapts to the user's Telegram theme while optionally keeping core site aesthetics.
- [ ] **MainButton Integration:** Use the Telegram `MainButton` for form submission, specifically calling `showProgress()` during API requests and `close()` upon success.

### 3. "Reply to Request" Form Implementation
- [ ] **Controller (View):** Create a view that:
  1. Accepts `request_id` and `token`.
  2. Validates them via `@tma_secure_required`.
  3. Retrieves request data from the database.
- [ ] **Template:** Create a "Letter blank" style page.
  - Fields: "To", "Subject" (pre-filled), and "Reply text".
- [ ] **Submission:** Clicking "Send" should trigger `Telegram.WebApp.showConfirm()` before proceeding with submission.

### 4. Telegram Bot Integration
- [ ] **URL Generation:** Add logic to the bot to create signed URLs using the same secret key as the backend.
- [ ] **Update Orchestrator:**
  - Replace the placeholder `_handler_reply_contact` in `NotificationsOrchestrator`.
  - Instead of `alert_text`, the bot returns a message with an inline button: `InlineKeyboardButton(text="✍️ Reply", web_app=WebAppInfo(url=signed_url))`.

### 5. Data Flow (Closing the Loop)
- [ ] **Handling the Reply:**
  - Form submission posts to a Django API endpoint.
  - Django queues an email delivery task via ARQ.
  - ARQ sends the actual email.
  - ARQ drops an event into a Redis Stream (`notification_status`) confirming if the email was delivered or if an error occurred.
- [ ] **UI Update in Bot:** The bot listens to the Redis stream and updates the admin channel message:
  - **Success:** Changes status to "Replied" and removes the "Reply" button.
  - **Error:** Updates status to "Error sending email" and retains the button for another attempt.
