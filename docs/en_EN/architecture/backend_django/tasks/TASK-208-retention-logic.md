# TASK-208: Smart Re-engagement Logic

[⬅️ Back to Roadmap](../roadmap.md)

## 🎯 Goal
Implement the backend logic to process the daily retention queue from Redis and generate personalized booking offers.

## 📋 Requirements

### 1. Service Layer (`RetentionService`)
- [ ] **`process_daily_retention()`**:
    - Receive a list of `client_id:service_id` from the Bot/Worker.
    - For each client:
        - Check if they have any **upcoming** appointments.
        - If NO upcoming appointments:
            - Fetch 4 available slots for the specific `service_id`.
            - Enqueue `send_reengagement_email` to ARQ with slot data.

### 2. API Layer (System API)
- [ ] **`POST /api/v1/system/notifications/process-reengagement/`**:
    - Secure endpoint (API Key required).
    - Receives the date or the list of targets from Redis.
    - Triggers the service method above.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-005: Smart Re-engagement](../../../global_task/TASK-GLOBAL-005-reengagement-campaign.md)
