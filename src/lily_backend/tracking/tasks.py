from __future__ import annotations

import asyncio

"""
ARQ tasks for tracking.

Wire into ARQ WorkerSettings:
    functions = [flush_tracking_to_db]
    cron_jobs = [cron(flush_tracking_to_db, minute={0, 30})]
"""


async def flush_tracking_to_db(ctx: dict) -> str:  # noqa: ARG001
    """Flush today's Redis page view counters into DB. Runs every 30 min."""
    from .flush import flush_page_views

    count = await asyncio.to_thread(flush_page_views)
    return f"flushed {count} paths"
