import asyncio

from codex_django.tracking.flush import flush_page_views


async def flush_tracking_to_db(ctx: dict) -> str:  # noqa: ARG001
    """Flush today's Redis page view counters into DB. Runs every 30 min."""
    count = await asyncio.to_thread(flush_page_views)
    return f"flushed {count} paths"
