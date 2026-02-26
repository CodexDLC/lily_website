# TASK-WRK-102: System Worker & Heartbeat Scheduler

[⬅️ Back to Global Task](../../../../global_task/TASK-GLOBAL-001-notifications-arq.md)

## 🎯 Goal
Implement a dedicated **System Worker** to handle background maintenance, recursive schedulers, and long-running tasks without affecting user-facing notifications.

## 🏗️ Architecture: Worker Roles

### 1. `notification-worker` (Existing)
- **Responsibility:** Immediate user-facing notifications (Booking confirmation, OTP, etc.).
- **Tasks:** `send_email_task`, `send_twilio_task`, `send_booking_notification_task`.
- **Goal:** Low latency for customer communication.

### 2. `system-worker` (New)
- **Responsibility:** Background maintenance, recursive schedulers, and heavy reporting.
- **Tasks:**
    - `hourly_notification_heartbeat`: Recursive heartbeat with `job_id="scheduler_hourly_heartbeat"`.
    - `daily_cleanup_task`: Log rotation and temporary data cleanup.
    - `analytics_report_task`: Heavy data aggregation for reports.
- **Goal:** Reliable execution of system-level background processes.

## 📋 Requirements for Heartbeat Task

- [ ] **Function:** `hourly_notification_heartbeat(ctx)`
- [ ] **Logic:**
    - Push `TRIGGER_REMINDERS` event to Redis Stream `lily:system:heartbeat`.
    - Reschedule itself using `_defer_by=3600` (1 hour).
    - Use fixed `_job_id="scheduler_hourly_heartbeat"` for monitoring in Django Admin.
- [ ] **Registration:** Add to a new `system_worker/tasks/task_aggregator.py`.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-001: Notifications & ARQ Integration](../../../../global_task/TASK-GLOBAL-001-notifications-arq.md)
