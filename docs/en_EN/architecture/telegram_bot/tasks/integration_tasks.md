# 🤖 Telegram Bot Integration Tasks

This document outlines the remaining tasks for the Telegram Bot integration.

> **Note:** Analytics, Reporting, and Delivery Tracking have been moved to the Django Admin Cabinet.

## 🔐 Authentication & Access Control

- [ ] **[TODO]** Update `StartOrchestrator` to parse `access_token` from `/start` payload for deep-linking.
- [ ] **[TODO]** Implement `AuthDataProvider` to verify tokens via Django API.
- [ ] **[TODO]** Implement `FeatureDiscoveryService` to filter available bot features based on user roles (Master/Admin/Client).
- [ ] **[TODO]** Ensure `BotMenuOrchestrator` dynamically updates based on permissions.

## 📡 Core Integration

- [ ] **[TODO]** Finalize callback handlers for appointment confirmation/rejection in `handlers.py`.
- [ ] **[TODO]** Implement secure API communication between Bot and Django (Shared Secret/JWT).

## ✅ Completed

- [x] **SendGrid API:** Implemented as fallback in `notification_worker`.
- [x] **Notification Orchestrator:** Implemented via Redis queue (`notification_worker`).
- [x] **Basic UI:** Notification cards and action buttons.
