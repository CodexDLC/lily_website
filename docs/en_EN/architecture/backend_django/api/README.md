# 🔌 API

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../README.md)

The `api` module handles the REST API for the application using **Django Ninja**.

## 📋 Overview

Django Ninja provides a fast, type-safe way to build APIs using standard Python type hints. This module centralizes all API endpoints, which are then mounted to the main URL configuration.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📄 Instance](./instance.md)** | The main `NinjaAPI` instance configuration. |
| **[📄 Routing](./urls.md)** | API routing and registration. |
| **[📄 Booking](./booking.md)** | Appointments and slots management for Telegram Bot. |
| **[📄 Promos](./promos.md)** | Public endpoints for active promos and tracking. |
| **[📄 Admin](./admin.md)** | Internal endpoints for cache refresh and contact processing. |

## 🛠️ Key Features

- **Automatic Docs:** Swagger/OpenAPI documentation generated automatically at `/api/docs`.
- **Type Safety:** Pydantic-like schemas (Ninja Schema) for request/response validation.
- **Async Support:** Support for asynchronous endpoints (used in `admin.py`).
- **Security:** X-API-Key authentication for sensitive endpoints.
