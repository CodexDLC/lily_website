# TASK-WRK-103: Feedback Email Task

## 🎯 Goal
Implement the worker-side function to send "Thank You" emails with review links.

## 📋 Requirements
- [ ] **Function:** `send_feedback_email(ctx, client_email, client_name, review_links)`
- [ ] **Logic:**
    - Render the HTML template (Thank you message).
    - Send via SendGrid API.
- [ ] **Registration:** Add to `system_worker/tasks/task_aggregator.py`.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-004: Post-Visit Feedback](../../../../global_task/TASK-GLOBAL-004-post-visit-feedback.md)
