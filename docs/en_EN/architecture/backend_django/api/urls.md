# 📄 API Routing

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Centralized API routing and registration for the `lily_website` project.

## 📋 Overview

The `api/urls.py` file defines versioned API routers. All endpoints are grouped under the `/v1/` prefix and mounted to the main `NinjaAPI` instance.

## 🗺️ Routing Map

| Prefix | Component | Description |
|:---|:---|:---|
| `/health/` | `health` | Health check endpoint (status=ok). |
| `/admin/` | `admin_router` | Admin API (Dashboard, etc.). |
| `/booking/` | `booking_router` | Booking API for Telegram Bot (appointment management). |
| `/promos/` | `promos_router` | Promos API (public, no auth). |

## 🛠️ Key Features

- **Versioned API:** Currently on version `v1`.
- **Modularity:** Each functional area (Admin, Booking, Promos) is defined in its own file and then registered here.
- **Future Support:** Placeholder for `stream_publisher_router` for Redis stream integration.
