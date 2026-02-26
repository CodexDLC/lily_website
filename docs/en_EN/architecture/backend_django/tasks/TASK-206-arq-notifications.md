# TASK-206: ARQ Notification System & Recursive Schedulers

[⬅️ Back to Roadmap](../roadmap.md)

## 🎯 Goal
Implement a robust, asynchronous notification system using ARQ with recursive scheduling (no cron required). The system will handle immediate booking confirmations and proactive reminders (24h and 3h before appointments).

## 📋 Requirements & Logic

### 1. Immediate Notifications
- [ ] **`send_booking_confirmation_task(appointment_id)`**: Triggered immediately after a successful booking. Sends Email/SMS to the client and a notification to the Admin/Master.

### 2. Recursive Schedulers (The "Heartbeat")
- [ ] **`hourly_notification_scheduler()`**: A recursive task that runs every hour.
    - [ ] **24h Check:** Finds appointments starting in 23-24 hours. Enqueues `send_reminder_24h_task`.
    - [ ] **3h Check:** Finds appointments starting in 2-3 hours. Enqueues `send_reminder_3h_task`.
    - [ ] **Self-Reschedule:** Enqueues itself to run again in 1 hour with a unique `job_id` to prevent duplicates.

### 3. Reminder Tasks
- [ ] **`send_reminder_24h_task(appointment_id)`**: Sends a "Day Before" reminder. Includes a link to cancel/reschedule (if allowed by policy).
- [ ] **`send_reminder_3h_task(appointment_id)`**: Sends a "Final" reminder (SMS/WhatsApp priority).

### 4. Safety & Policy
- [ ] **Status Validation:** Every task must verify the appointment status (e.g., not `cancelled`) before sending anything.
- [ ] **Idempotency:** Use unique `job_id` for schedulers to ensure only one instance of the heartbeat is running.

## 🛠️ Implementation Steps
1. [ ] **Infrastructure:** Verify Redis AOF/Persistence is active (Done ✅).
2. [ ] **Core:** Implement `DjangoArqClient` in `core/arq/client.py` (Done ✅).
3. [ ] **Tasks:** Create `features/booking/tasks.py` with the logic above.
4. [ ] **Integration:** Add a "Bootstrap" trigger to start the `hourly_notification_scheduler` on server startup.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-001: Notifications & ARQ](../../../global_roadmap.md)
