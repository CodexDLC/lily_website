# 📂 Cabinet Feature

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../README.md)

The `cabinet` feature handles admin and manager-facing logic for the Lily project.

## 📋 Overview

The Cabinet is a set of services and views for administrative tasks, such as managing appointments and processing contact requests. It provides the backend logic for the manager's dashboard.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📄 Appointment Service](./appointment_service.md)** | High-level business logic for appointment management (e.g., rescheduling). |
| **[📄 Selectors](./selector/README.md)** | Data retrieval logic for the dashboard. |
| **[📄 Views](./views/README.md)** | Admin-specific views and UI logic. |

## 🛠️ Key Features

- **Dashboard Integration:** Works with `System` features to maintain a fast, Redis-backed dashboard.
- **Appointment Rescheduling:** Sophisticated logic for proposing new slots to clients.
- **Manager Tools:** Services for processing incoming requests and tracking system state.
