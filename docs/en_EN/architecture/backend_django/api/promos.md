# 📄 Promos API

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Public endpoints for retrieving and tracking active promo messages.

## 📋 Overview

The Promos API provides endpoints for the frontend to fetch current promo messages and track views and clicks on those promos.

## 🗺️ Component Map

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/active/` | Get active promo for the current page (supports filtering by `page_slug`). |
| `POST` | `/{id}/track-view/` | Track that a promo was viewed (floating button shown). |
| `POST` | `/{id}/track-click/` | Track that a promo was clicked (modal opened). |

## 🛠️ Key Logic

- **Public Access:** No authentication required for these endpoints.
- **Service Layer Integration:** Uses `PromoService` to check promo status and record tracking events.
- **Image URLs:** Build absolute URLs for promo images using `request.build_absolute_uri`.
- **Display Delay:** Includes `display_delay` in the response to control when the promo appears on the frontend.
