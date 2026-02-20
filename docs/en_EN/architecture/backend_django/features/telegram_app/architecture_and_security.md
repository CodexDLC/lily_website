# 📄 Architecture & Security

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

This document describes the architectural approach and security mechanisms for integrating Telegram Mini Apps (TMA) with the backend.

## 🔐 Security Principles

The primary goal is to ensure that administrative TMA pages can *only* be opened:
1. From inside the Telegram client.
2. By the authenticated administrator who received the message.
3. For the specific request intent.

### 1. HMAC URL Signing

When the bot generates an inline button to open the web app, it constructs a URL with a cryptographic signature.

*   **Payload:** `request_id`, timestamp (`exp`), `action` (e.g., `reply`).
*   **Signature:** `HMAC-SHA256(payload, SECRET_KEY)`.
*   **Purpose:** Prevents users from guessing URLs or modifying the `request_id` to access other requests.

### 2. Telegram WebApp Data Validation (`initData`)

Telegram provides `Telegram.WebApp.initData` which contains user information and a cryptographic hash generated using the bot's token.

*   **Validation:** The backend verifies this hash against the bot token.
*   **Purpose:** Guarantees the request originated from the Telegram app and identifies the exact Telegram User ID making the request.

### 3. The `@tma_secure_required` Decorator

This custom decorator wraps all TMA views in Django.

**Flow:**
1. Extract HMAC signature from URL query parameters.
2. Extract `initData` (either passed via headers in API calls or via POST body in initial load).
3. Validate HMAC signature (is it valid? is it expired?).
4. Validate `initData` against Bot Token.
5. If both pass -> inject verified `user_id` into the request context -> Serve page.
6. If either fails -> Return 403 Forbidden or 404 Not Found.
