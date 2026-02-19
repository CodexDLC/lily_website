# 📜 Core Tasks

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Shared task definitions available to all workers.

**File:** `src/workers/core/tasks.py`

## `requeue_to_stream`

```python
async def requeue_to_stream(ctx, stream_name: str, payload: dict) -> None:
```

Universal task for returning a message to a Redis Stream. Used by the bot for retry handling on failures.

### Behavior

1. Retrieves `StreamManager` from the ARQ context.
2. Increments the `_retries` counter in the payload.
3. If retries exceed **5**, drops the message and logs an error.
4. Otherwise, re-adds the event to the specified stream.

## `CORE_FUNCTIONS`

```python
CORE_FUNCTIONS = [requeue_to_stream]
```

List of base tasks included in every worker via the task aggregator.
