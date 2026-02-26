# TASK-BOT-102: System Orchestrator (Redis Stream Listener)

## 🎯 Goal
Implement the Bot's role as an orchestrator that listens to system signals from Redis Streams and triggers the corresponding Django API endpoints.

## 📋 Requirements

### 1. Redis Stream Listener
- [ ] Monitor stream `lily:system:heartbeat`.
- [ ] Handle events:
    - `TRIGGER_REMINDERS`: Call Django `process-reminders` API.
    - `TRIGGER_POST_VISIT`: Call Django `process-post-visit` API.
    - `TRIGGER_RETENTION`: Call Django `process-reengagement` API.

### 2. Django API Client
- [ ] Implement a secure HTTP client to communicate with the Django System API.
- [ ] Use `BACKEND_API_KEY` for authentication.

## 🔗 Global Task Reference
Part of [TASK-GLOBAL-001: Notifications & ARQ](../../../global_task/TASK-GLOBAL-001-notifications-arq.md)
