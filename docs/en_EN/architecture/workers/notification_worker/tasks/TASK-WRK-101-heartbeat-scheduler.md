# TASK-WRK-101: Heartbeat Scheduler & Worker Separation

[⬅️ Back to Global Task](../../../../global_task/TASK-GLOBAL-001-notifications-arq.md)

## 🎯 Goal
Implement the "Heartbeat" recursive task and separate workers into "Instant" and "Scheduled" pools for better scalability and reliability.

## 🏗️ Architecture: Worker Separation

### 1. `worker-instant` (High Priority)
- **Responsibility:** Immediate user-facing notifications (Booking confirmation, OTP, etc.).
- **Tasks:** `send_email_task`, `send_twilio_task`, `send_booking_notification_task`.
- **Scaling:** Multiple replicas if needed.

### 2. `worker-scheduled` (System Priority)
- **Responsibility:** Background maintenance, recursive schedulers, and heavy reporting.
- **Tasks:** `hourly_notification_heartbeat`, `daily_cleanup_task`, `analytics_report_task`.
- **Scaling:** Single replica is usually enough to prevent duplicate scheduling.

## 📋 Requirements for Heartbeat Task

- [ ] **Function:** `hourly_notification_heartbeat(ctx)`
- [ ] **Logic:**
    - Push `TRIGGER_REMINDERS` event to Redis Stream `lily:system:heartbeat`.
    - Reschedule itself using `_defer_by=3600` (1 hour).
    - Use fixed `_job_id="scheduler_hourly_heartbeat"` for monitoring.
- [ ] **Registration:** Add to `task_aggregator.py`.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-001: Notifications & ARQ Integration](../../../../global_task/TASK-GLOBAL-001-notifications-arq.md)
