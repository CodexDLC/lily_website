# 🌍 LILY Project Global Roadmap

This document tracks the high-level progress of the entire LILY ecosystem (Website, Backend, Telegram Bot, Infrastructure).

## 📌 Current Focus: Notifications, Retention & Analytics

| Global Task | Status | Progress | Domain(s) |
|:---|:---:|:---:|:---|
| **[TASK-GLOBAL-001: Notifications & ARQ](./global_task/TASK-GLOBAL-001-notifications-arq.md)** | 🔄 In Progress | 20% | Backend, Infrastructure |
| **[TASK-GLOBAL-004: Post-Visit Feedback](./global_task/TASK-GLOBAL-004-post-visit-feedback.md)** | 📝 Design | 0% | Backend, Worker |
| **[TASK-GLOBAL-005: Smart Re-engagement](./global_task/TASK-GLOBAL-005-reengagement-campaign.md)** | 📝 Design | 0% | Backend, Redis, Worker |
| **[TASK-GLOBAL-007: CRM Analytics System](./global_task/TASK-GLOBAL-007-analytics-system.md)** | 📝 Design | 0% | Backend (Cabinet) |
| **[TASK-210: Contact Requests in Cabinet](./architecture/backend_django/tasks/TASK-210-contact-requests-cabinet.md)** | 📝 Ready | 0% | Backend (Cabinet) |
| **[TASK-GLOBAL-006: Database Backups](./global_task/TASK-GLOBAL-006-database-backups.md)** | ⏸️ On Hold | 0% | Infrastructure |
| **[TASK-GLOBAL-002: QR Finalization System](#-task-global-002-qr-finalization-system)** | 📝 Design | 5% | Backend, Bot |
| **[TASK-GLOBAL-003: Production Deployment](#-task-global-003-production-deployment)** | 📝 Ready | 0% | Infrastructure |

---

## 🚀 TASK-GLOBAL-001: Notifications & ARQ
**Goal:** Robust asynchronous reminders (26h and 3h before) + System Health Alarms.

- [x] **Infrastructure:** Setup Redis and ARQ worker (Done ✅).
- [ ] **Backend:** [TASK-206: ARQ Integration & Email Tasks](./architecture/backend_django/tasks/TASK-206-arq-notifications.md)
- [ ] **Admin:** Dashboard Monitoring (✅/❌) & Health Alerts.

---

## 💅 TASK-GLOBAL-004: Post-Visit Feedback
**Goal:** Automated "Thank You" messages and review requests.

- [ ] **Backend:** [TASK-207: Feedback Logic & API](./architecture/backend_django/tasks/TASK-207-feedback-logic.md)
- [ ] **Worker:** [TASK-WRK-103: Feedback Email Task](./architecture/workers/system_worker/tasks/TASK-WRK-103-feedback-email.md)

---

## 🔄 TASK-GLOBAL-005: Smart Re-engagement
**Goal:** Service-specific retention based on lifecycle.

- [ ] **Backend:** [TASK-208: Service Lifecycle & Redis Queue](./architecture/backend_django/tasks/TASK-208-retention-logic.md)
- [ ] **Worker:** [TASK-WRK-104: Retention Email Task](./architecture/workers/system_worker/tasks/TASK-WRK-104-retention-email.md)

---

## 📊 TASK-GLOBAL-007: CRM Analytics System
**Goal:** Business insights and reporting layer in the Admin Cabinet.

- [ ] **Backend:** [TASK-209: Analytics & Reporting Layer](./architecture/backend_django/tasks/TASK-209-analytics-reporting-layer.md)

---

## 🛠️ Domain Roadmaps (Deep Dive)
- [Django Backend Roadmap](./architecture/backend_django/roadmap.md)
- [Telegram Bot Tasks](./architecture/telegram_bot/tasks/README.md)
