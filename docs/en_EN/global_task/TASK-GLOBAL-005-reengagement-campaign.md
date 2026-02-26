# TASK-GLOBAL-005: Smart Re-engagement (Service Lifecycle)

## 🎯 Overview
Automated retention system based on the specific lifecycle of each service. Instead of a generic "one size fits all" reminder, the system calculates the ideal return date for every client.

---

## ⚙️ Core Logic: Service-Specific Lifecycle

1. **Service Configuration:**
    - Each `Service` model in Django gets a `retention_days` field (e.g., Manicure: 21, Haircut: 30, Coloring: 60).

2. **The Redis "Retention Queue":**
    - When an appointment is marked as `completed`:
        - Django calculates `target_date = completion_date + service.retention_days`.
        - Django adds a record to Redis: `SADD retention:YYYY-MM-DD "client_id:service_id"`.

3. **The Daily Check (Heartbeat):**
    - The `system-worker` triggers a daily check for the current date's Redis key.
    - **Validation (Django API):** For each entry, the system checks if the client *already* has an upcoming appointment.
    - **Action:** If no upcoming appointment exists, the system enqueues a personalized `send_reengagement_email` task.

---

## 🏗️ Layer Responsibilities & Sub-Tasks

### 1. Django Backend Layer
- [ ] **[TASK-208: Retention Logic & Redis Queue](../architecture/backend_django/tasks/TASK-208-retention-logic.md)**
- [ ] **Model Update:** Add `retention_days` to `Service` model.

### 2. Telegram Bot Layer
- [ ] **[TASK-BOT-102: System Orchestrator](../architecture/telegram_bot/tasks/TASK-BOT-102-system-orchestrator.md)**
- [ ] **Daily Trigger:** Listen for the daily heartbeat and trigger the Django retention processor.

### 3. ARQ Worker Layer
- [ ] **[TASK-WRK-104: Retention Email Task](../architecture/workers/system_worker/tasks/TASK-WRK-104-retention-email.md)**

### 4. Infrastructure Layer (Redis)
- [ ] **Queue Management:** Logic to read from the Redis date-based sets.

---

## 🔗 Status Tracking
- **Current Status:** 📝 Design & Documentation (Added: Cross-links to sub-tasks)
- **Next Milestone:** Update `Service` model and implement Redis queue logic.
