from unittest.mock import patch

import pytest
from system.tasks.tracking import flush_tracking_to_db


class TestSystemTasks:
    @pytest.mark.asyncio
    async def test_flush_tracking_to_db_logic(self):
        # Mocking the actual logic that runs in a thread
        with patch("system.tasks.tracking.flush_page_views", return_value=5) as mock_flush:
            ctx = {}
            result = await flush_tracking_to_db(ctx)

            assert "flushed 5 paths" in result
            mock_flush.assert_called_once()
