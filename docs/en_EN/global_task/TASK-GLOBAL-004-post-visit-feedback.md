# TASK-GLOBAL-004: Post-Visit Processing (Feedback & Retention Scheduling)

## 🎯 Overview
A unified process to handle clients after a successful visit. It combines immediate gratitude (feedback request) with long-term retention (scheduling the next visit reminder).

---

## 🔄 The "Post-Visit" Flow (Step-by-Step)

1. **Trigger:**
    - The `hourly_heartbeat` from the Worker signals the Bot.
    - The Bot calls Django API: `POST /api/v1/system/notifications/process-post-visit/`.

2. **Django Backend (The Brain):**
    - Finds appointments with `status == 'completed'` and `feedback_sent == False`.
    - **Action 1 (Feedback):** Enqueues `send_feedback_email` task into ARQ.
    - **Action 2 (Retention Scheduling):**
        - Calculates `target_date = now + service.retention_days`.
        - Writes to Redis: `SADD retention:YYYY-MM-DD "client_id:service_id"`.
    - **Action 3 (Mark Processed):** Sets `feedback_sent = True`.

3. **ARQ Worker (The Executor):**
    - Sends the "Thank You" email with review links.

---

## 🏗️ Layer Responsibilities & Sub-Tasks

### 1. Django Backend Layer
- [ ] **[TASK-207: Feedback Logic & API](../architecture/backend_django/tasks/TASK-207-feedback-logic.md)**
- [ ] **Model Update:** Add `feedback_sent` (BooleanField) to `Appointment`.

### 2. Telegram Bot Layer
- [ ] **[TASK-BOT-102: System Orchestrator](../architecture/telegram_bot/tasks/TASK-BOT-102-system-orchestrator.md)**
- [ ] **Trigger Logic:** Handle the `TRIGGER_POST_VISIT` signal.

### 3. ARQ Worker Layer
- [ ] **[TASK-WRK-103: Feedback Email Task](../architecture/workers/system_worker/tasks/TASK-WRK-103-feedback-email.md)**

### 4. Infrastructure Layer (Redis)
- [ ] **Retention Queue:** Date-based sets (`retention:YYYY-MM-DD`) to store future re-engagement targets.

---

## 🔗 Status Tracking
- **Current Status:** 📝 Design & Documentation (Added: Cross-links to sub-tasks)
- **Next Milestone:** Implement the dual-action service in Django.
