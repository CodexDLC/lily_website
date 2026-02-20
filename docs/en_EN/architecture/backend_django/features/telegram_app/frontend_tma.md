# 📄 Frontend (TMA)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

This document details the frontend implementation for the Telegram Mini App interface.

## 🎨 Design Philosophy

The TMA should feel like a native extension of Telegram. While it can maintain subtle hints of the main site's branding (like specific accent colors or font choices), its primary layout, background, and text colors **must** adapt to the user's active Telegram theme.

## 🧱 The Base Template (`tma_base.html`)

All TMA pages inherit from this base template.

### Key Inclusions:
1.  **Telegram WebApp JS:** `<script src="https://telegram.org/js/telegram-web-app.js"></script>`
2.  **Theme CSS Variables:** CSS that mapping standard elements to Telegram's dynamic variables:
    *   `var(--tg-theme-bg-color)`
    *   `var(--tg-theme-text-color)`
    *   `var(--tg-theme-hint-color)`
    *   `var(--tg-theme-button-color)`
    *   `var(--tg-theme-button-text-color)`

## 🎯 Form Interactions & MainButton

To provide a seamless experience, we heavily utilize `Telegram.WebApp` API.

1.  **Initialization:** Call `Telegram.WebApp.ready()` on page load.
2.  **Form Data:** The form itself is a standard HTML form, but its submission is intercepted by JavaScript.
3.  **MainButton:**
    *   Configure the main button at the bottom of the TMA: `Telegram.WebApp.MainButton.setText('Send Reply').show()`.
    *   When the user types, the button can become active.
4.  **Submission Flow:**
    *   User clicks the MainButton.
    *   Optional: Call `Telegram.WebApp.showConfirm()` to verify intent.
    *   Call `Telegram.WebApp.MainButton.showProgress()`.
    *   Execute AJAX/Fetch request to the Django backend.
    *   On Success: Call `Telegram.WebApp.close()` to dismiss the app smoothly.
