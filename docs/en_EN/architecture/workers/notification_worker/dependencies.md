# 📜 Notification Worker Dependencies

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Dependency injection setup for the Notification Worker.

**File:** `src/workers/notification_worker/dependencies.py`

## Startup Dependencies

Executed in order during `worker_startup`:

| Function | Injects | Description |
|:---|:---|:---|
| `init_common_dependencies` | Redis, SiteSettings | From `core.base_module.dependencies` |
| `init_arq_service` | `arq_service` | Creates `ArqService` for job enqueueing |
| `init_stream_manager` | `stream_manager` | Creates `StreamManager` from Redis |
| `init_notification_service` | `notification_service` | Email rendering + SMTP + URL generation |
| `init_twilio_service` | `twilio_service` | SMS/WhatsApp via Twilio (optional) |

## Shutdown Dependencies

| Function | Description |
|:---|:---|
| `close_arq_service` | Closes the ARQ connection |
| `close_common_dependencies` | Closes Redis and other shared services |

## Key Detail

`init_twilio_service` gracefully handles missing Twilio credentials — sets `ctx["twilio_service"] = None` and logs a warning instead of raising.
