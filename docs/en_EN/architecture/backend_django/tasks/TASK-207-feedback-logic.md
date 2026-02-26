# TASK-207: Post-Visit Feedback & Retention Logic

[⬅️ Back to Roadmap](../roadmap.md)

## 🎯 Goal
Implement the backend logic to handle clients after their visit: sending "Thank You" emails and scheduling future re-engagement in Redis.

## 📋 Requirements

### 1. Model Updates
- [ ] Add `feedback_sent` (BooleanField, default=False) to `Appointment` model.
- [ ] Add `retention_days` (PositiveIntegerField, default=30) to `Service` model.

### 2. Service Layer (`BookingNotificationService`)
- [ ] **`process_post_visit_actions()`**:
    - Find appointments: `status == 'completed'` AND `feedback_sent == False`.
    - For each:
        - Enqueue `send_feedback_email` to ARQ.
        - Calculate `target_date = now + service.retention_days`.
        - Push to Redis: `SADD retention:YYYY-MM-DD "client_id:service_id"`.
        - Set `feedback_sent = True`.

### 3. API Layer (System API)
- [ ] **`POST /api/v1/system/notifications/process-post-visit/`**:
    - Secure endpoint (API Key required).
    - Triggers the service method above.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-004: Post-Visit Feedback](../../../global_task/TASK-GLOBAL-004-post-visit-feedback.md)
