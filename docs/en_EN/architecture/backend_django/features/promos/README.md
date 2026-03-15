# 📂 Promos Feature

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../README.md)

The `promos` feature handles management, display, and tracking of promotional messages (popups or floating buttons) on the website.

## 📋 Overview

Promos are designed to be dynamic and trackable. They can be assigned to specific pages and track user interactions (views and clicks).

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📄 PromoMessage](./promo_message.md)** | The main model defining promo content, styles, and tracking data. |
| **[📄 PromoService](./promo_service.md)** | Business logic for fetching active promos and updating tracking statistics. |

## 🛠️ Key Features

- **Dynamic Styling:** Admins can configure button colors, text colors, and display delays.
- **Tracking:** Automatically increments view and click counters.
- **Page Targeting:** Promos can be filtered by `page_slug` to show specific messages on specific pages.
- **Multilingual Support:** Integration with `translation.py` for localized promo content.
