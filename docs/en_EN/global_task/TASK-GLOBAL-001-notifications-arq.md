# TASK-GLOBAL-001: Notifications & ARQ Integration (Isolated Worker Architecture)

## 🎯 Overview
Implementation of a robust, asynchronous notification system using a "Heartbeat" pattern.
**Architecture:** The Worker is isolated (Redis only). The Telegram Bot acts as an Orchestrator between the Worker and the Django API.

---

## 🔄 The "Heartbeat" Flow (Step-by-Step)

1. **ARQ Worker (The Timer):**
    - Runs a recursive task `hourly_heartbeat` every hour.
    - **Action:** Pushes a "TRIGGER_REMINDERS" event into a **Redis Stream**.
    - **Recursion:** Enqueues itself for the next hour.

2. **Telegram Bot (The Orchestrator):**
    - Listens to the Redis Stream (via a dedicated service/feature).
    - **Action:** Upon receiving the event, calls the Django API: `POST /api/v1/system/notifications/process-reminders/`.

3. **Django Backend (The Brain):**
    - Receives the API call from the Bot.
    - **Action:** Queries the DB for appointments starting in **26h** (Day before + 2h buffer for cancellation) and **3h**.
    - **Action:** For each appointment, enqueues specific tasks (`send_email`, `send_sms`) back into ARQ.

4. **ARQ Worker (The Executor):**
    - Picks up the specific notification tasks and sends them to recipients.

---

## 🚨 System Health Alarm (Monitoring)

To ensure the system is always running, we implement a "Dead Man's Switch" logic:
- **Logic:** Django monitors the last successful execution of `hourly_heartbeat` in Redis.
- **Alerting:** If the heartbeat is missing for more than 75 minutes:
    - The Bot sends a message to the Admin Telegram Chat:
      `⚠️ CRITICAL: System Heartbeat lost! Notification engine might be down.`
- **Dashboard:** Visual ✅/❌ indicators in the Admin Cabinet.

---

## 🏗️ Layer Responsibilities & Sub-Tasks

### 1. Django Backend Layer
- [ ] **[TASK-206: API & Logic Reminders](../architecture/backend_django/tasks/TASK-206-arq-notifications.md)**
- [ ] **Monitoring Service:** Logic to check Redis for the heartbeat and trigger Telegram alerts if lost.
- [ ] **Admin Dashboard:** Monitor the `hourly_heartbeat` job status in Redis (✅/❌) and provide a "Force Start" button.

### 2. Telegram Bot Layer
- [ ] **[TASK-BOT-102: System Orchestrator](../architecture/telegram_bot/tasks/TASK-BOT-102-system-orchestrator.md)**
- [ ] **Alerting:** Send system health alerts to the designated admin chat.

### 3. ARQ Worker Layer
- [ ] **[TASK-WRK-102: System Heartbeat Task](../architecture/workers/system_worker/tasks/TASK-WRK-102-system-heartbeat.md)**
- [ ] **Notification Tasks:** Functions to send Email (SendGrid) and SMS (Twilio).

### 4. Infrastructure Layer (Redis)
- [x] **Persistence:** AOF/RDB enabled (Done ✅).
- [ ] **Streams:** Define the stream name for the heartbeat signal.

---

## 🔗 Status Tracking
- **Current Status:** 📝 Design & Documentation (Added: Cross-links to sub-tasks)
- **Next Milestone:** Define the Redis Stream contract and Django API schema.
