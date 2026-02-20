# 🤖 Telegram Bot Integration Tasks

This document outlines the remaining tasks for the Telegram Bot integration, focusing on analytics and delivery tracking.

## 📊 Analytics & Reporting (High Priority)

- [ ] **[TODO]** Backend: Implement `AnalyticsService` to aggregate revenue (Total & Per Master).
- [ ] **[TODO]** Data Structuring: Format data into "Cross-Table" JSON (Rows: Dates, Cols: Masters, Cells: Revenue).
- [ ] **[TODO]** Integration: Store structured JSON in Redis for Arc/Worker access.
- [ ] **[TODO]** Arc Task: Implement worker task to generate Excel/PDF report from Redis data.
- [ ] **[TODO]** Delivery: Implement email sending logic for the generated report.

## 📡 Delivery Tracking (Twilio)

- [ ] **[TODO]** Configure **Twilio Webhooks** to track WhatsApp/SMS delivery status in real-time.
  - *Goal:* Update notification status in Admin Panel (Sent -> Delivered/Failed).
- [ ] **[TODO]** Create unified templates for all channels (Email HTML, WhatsApp Buttons, SMS Text).

## 🔐 Authentication (On Hold)

- [ ] **[ON HOLD]** Update `StartOrchestrator` to parse `access_token` from `/start` payload.
- [ ] **[ON HOLD]** Implement real `AuthDataProvider` to call Django API for user linking.
- [ ] **[ON HOLD]** Update `FeatureDiscoveryService` to support filtering by `is_admin`.
- [ ] **[ON HOLD]** Ensure `BotMenuOrchestrator` only shows non-admin features.

## ✅ Completed

- [x] **SendGrid API:** Implemented as fallback in `notification_worker`.
- [x] **Notification Orchestrator:** Implemented via Redis queue (`notification_worker`).
