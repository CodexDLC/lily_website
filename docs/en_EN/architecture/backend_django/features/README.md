# 🧩 Features (Django Apps)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../README.md)

This directory (`src/backend_django/features`) contains the modular Django applications, each representing a distinct feature or domain of the project.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📂 Main](./main/README.md)** | Core website pages, services, and base models. |
| **[📂 System](./system/README.md)** | Infrastructure services, site settings, and Redis managers. |
| **[📂 Booking](./booking/README.md)** | Business logic for appointment booking and slot management. |
| **[📂 Promos](./promos/README.md)** | Management and tracking of promotional messages. |
| **[📂 Cabinet](./cabinet/README.md)** | Admin/Manager dashboard and personal cabinet logic. |

## 🏗️ Purpose

Organizing the backend into features (Django apps) helps to:
*   **Improve Modularity:** Each feature is a self-contained unit.
*   **Enhance Scalability:** Easier to manage and scale individual parts of the application.
*   **Increase Maintainability:** Changes in one feature are less likely to impact others.
*   **Facilitate Team Collaboration:** Different teams can work on different features concurrently.
