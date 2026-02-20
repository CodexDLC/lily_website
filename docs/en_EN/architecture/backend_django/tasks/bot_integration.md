# 🤖 Bot Integration Tasks (Cancelled/On Hold)

**Status:** 🛑 **CANCELLED / ON HOLD**
**Reason:** GDPR/DSGVO Compliance & Business Decision.

Direct linking of Telegram IDs to Client profiles without explicit, complex consent is a privacy risk in Germany. The booking flow (`step_5_success.html`) will remain clean and focused on confirmation, without social login buttons.

## ❌ Cancelled Tasks

- [x] **[CANCELLED]** Add `telegram_id` (BigIntegerField, unique=True) to `features.booking.models.Client`.
- [x] **[CANCELLED]** Create migration for `Client` model.
- [x] **[CANCELLED]** Create endpoint `POST /api/bot/link-client/` to link `telegram_id` using `access_token`.
- [x] **[CANCELLED]** Create endpoint `GET /api/bot/client-stats/` for `DashboardAdmin`.
- [x] **[CANCELLED]** Update `step_5_success.html` (Booking) with "Connect Telegram" button.
- [x] **[CANCELLED]** Update Contact Form success page with "Connect Telegram" button.
- [x] **[CANCELLED]** Update `send_booking_notification_task` to include Telegram delivery if `telegram_id` is present.

## ✅ Completed Alternatives

- [x] **Admin Notifications:** Telegram notifications are sent to admins via Redis queue (`notification_worker`), not directly to clients.
- [x] **Email/SMS:** Client notifications are handled via Email (SMTP/SendGrid) and SMS (Twilio).
