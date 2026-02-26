# TASK-WRK-104: Retention Email Task

## 🎯 Goal
Implement the worker-side function to send personalized re-engagement offers.

## 📋 Requirements
- [ ] **Function:** `send_reengagement_email(ctx, client_email, client_name, service_title, available_slots)`
- [ ] **Logic:**
    - Render the HTML template (We miss you + suggested slots).
    - Send via SendGrid API.
- [ ] **Registration:** Add to `system_worker/tasks/task_aggregator.py`.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-005: Smart Re-engagement](../../../../global_task/TASK-GLOBAL-005-reengagement-campaign.md)
