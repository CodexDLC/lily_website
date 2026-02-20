# 📜 Notification Worker Entry Point

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Main ARQ worker definition for the Notification Worker.

**File:** `src/workers/notification_worker/worker.py`

## Lifecycle

### `worker_startup(ctx)`

1. Initializes logging via `setup_logging(settings, "notification_worker")`.
2. Calls `base_startup(ctx)` for common initialization.
3. Iterates through `STARTUP_DEPENDENCIES` and initializes each.

### `worker_shutdown(ctx)`

1. Iterates through `SHUTDOWN_DEPENDENCIES` and closes each.
2. Calls `base_shutdown(ctx)` for common cleanup.

## `WorkerSettings` Class

Extends `BaseArqSettings` with ARQ-specific configuration:

| Setting | Source |
|:---|:---|
| `redis_settings` | `settings.effective_redis_host`, port, password |
| `max_jobs` | `settings.arq_max_jobs` |
| `job_timeout` | `settings.arq_job_timeout` |
| `keep_result` | `settings.arq_keep_result` |
| `functions` | Aggregated from `task_aggregator.FUNCTIONS` |
