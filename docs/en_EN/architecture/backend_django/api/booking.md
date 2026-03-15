# 📄 Booking API

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Endpoints for managing appointments, primarily used by the Telegram Bot for admin tasks.

## 📋 Overview

The Booking API provides methods for confirming or cancelling appointments, retrieving available slots for rescheduling, and getting summaries of appointments by category.

## 🗺️ Component Map

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/appointments/manage/` | Universal endpoint for confirming or cancelling appointments. |
| `GET` | `/slots/` | Returns available slots starting from a cancelled appointment date. |
| `POST` | `/appointments/propose/` | Cancels appointment (reason: reschedule) and proposes alternative slot. |
| `POST` | `/appointments/expire/` | Automatically cancels unconfirmed appointments after 24h. |
| `GET` | `/appointments/summary/` | Summary of appointments by service category (total/pending/completed). |
| `GET` | `/appointments/list/` | Paginated list of appointments for a specific category. |

## 🛠️ Key Logic

- **Authentication:** Protected by `BotApiKey` (requires `X-API-Key` header matching `BOT_API_KEY` in settings).
- **Service Layer Integration:** Uses `SlotService` for finding free slots and `AppointmentService.propose_reschedule` for handling rescheduling logic.
- **Cache Synchronization:** Triggers `NotificationCacheManager.seed_appointment` when appointment status changes to notify the notification worker.
