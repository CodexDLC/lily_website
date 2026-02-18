# 📋 Bot & Notifications Integration Tasks

## 🛠 Feature: Commands (Welcome Screen)
- [x] Update `texts.py` with `WELCOME_USER` and `WELCOME_ADMIN`.
- [x] Update `keyboards.py` to support `is_admin` flag and `DashboardCallback`.
- [x] Update `StartOrchestrator` to check admin rights via `BotSettings`.
- [ ] **[TODO]** Update `StartOrchestrator` to parse `access_token` from `/start` payload.
- [ ] **[TODO]** Implement real `AuthDataProvider` to call Django API for user linking.

## 🛠 Feature: Bot Menu
- [ ] **[TODO]** Update `FeatureDiscoveryService` to support filtering by `is_admin`.
- [ ] **[TODO]** Ensure `BotMenuOrchestrator` only shows non-admin features.

## 🛠 Feature: Dashboard Admin (New)
- [ ] Create feature structure via `manage.py`.
- [ ] Implement `DashboardAdminOrchestrator` to show admin-only features.
- [ ] Create UI for admin statistics and system management.

## 📊 Feature: Analytics & Reporting
- [ ] **[TODO]** Backend: Implement `AnalyticsService` to aggregate revenue (Total & Per Master).
- [ ] **[TODO]** Data Structuring: Format data into "Cross-Table" JSON (Rows: Dates, Cols: Masters, Cells: Revenue).
- [ ] **[TODO]** Integration: Store structured JSON in Redis for Arc/Worker access.
- [ ] **[TODO]** Arc Task: Implement worker task to generate Excel/PDF report from Redis data.
- [ ] **[TODO]** Delivery: Implement email sending logic for the generated report.

## 📱 Feature: Multi-Channel Notifications (Twilio & SendGrid)
- [ ] **[TODO]** Implement `NotificationOrchestrator` (Python):
    - Trigger: `send_all(client, message, attachment=None)`.
    - Step 1: Send **Email** (Always - via SendGrid/SMTP).
    - Step 2: Try **WhatsApp** via Twilio (Rich content & buttons).
    - Step 3: If WhatsApp fails (webhook/error) -> Send **SMS** (Fallback).
- [ ] **[TODO]** Setup **SendGrid API** for professional HTML emails and Excel attachments.
- [ ] **[TODO]** Configure **Twilio Webhooks** to track WhatsApp delivery status in real-time.
- [ ] **[TODO]** Create unified templates for all channels (Email HTML, WhatsApp Buttons, SMS Text).

## ⚙️ Core & Infrastructure
- [ ] Add `telegram_id` linking logic to the DI container.
