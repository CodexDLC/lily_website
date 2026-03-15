# 📄 Admin API

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Internal endpoints for cache management and administrative tasks.

## 📋 Overview

The Admin API provides endpoints to refresh Redis cache for the dashboard and to mark contact requests as processed.

## 🗺️ Component Map

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/cache/refresh/` | Triggers a full refresh of admin dashboard data in Redis. |
| `POST` | `/contacts/{id}/process/` | Marks a contact request as processed and refreshes cache. |

## 🛠️ Key Logic

- **Authentication:** Protected by `BotApiKey` (requires `X-API-Key` header matching `BOT_API_KEY` in settings).
- **Async Support:** Uses `async` endpoints for potentially long-running cache refresh operations.
- **Service Layer Integration:** Uses `DashboardRefreshService` to handle complex Redis data aggregation.
- **Database Integration:** Direct access to `ContactRequest` model for updating status.
