import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from workers.core.heartbeat import HeartbeatTask, WorkerHeartbeatRegistry


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def registry(mock_redis):
    return WorkerHeartbeatRegistry(mock_redis)


@pytest.fixture
def sample_task():
    return HeartbeatTask(
        task_id="test.task", domain="test", queue_name="default", expected_interval_sec=60, stale_after_sec=120
    )


class TestWorkerHeartbeatRegistry:
    @pytest.mark.asyncio
    async def test_should_run_enabled_and_lock_available(self, registry, mock_redis):
        mock_redis.hget.return_value = "1"
        mock_redis.set.return_value = True

        should = await registry.should_run("test.task", lock_ttl_sec=100)

        assert should is True
        mock_redis.hget.assert_called_with("worker:tasks:test.task", "enabled")
        mock_redis.set.assert_called_with("worker:tasks:test.task:lock", "1", ex=100, nx=True)

    @pytest.mark.asyncio
    async def test_should_not_run_disabled(self, registry, mock_redis):
        mock_redis.hget.return_value = "0"

        should = await registry.should_run("test.task", lock_ttl_sec=100)

        assert should is False
        mock_redis.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_not_run_locked(self, registry, mock_redis):
        mock_redis.hget.return_value = "1"
        mock_redis.set.return_value = False

        should = await registry.should_run("test.task", lock_ttl_sec=100)

        assert should is False

    @pytest.mark.asyncio
    async def test_mark_started(self, registry, mock_redis, sample_task):
        await registry.mark_started(sample_task, job_id="123")

        mock_redis.hset.assert_called_once()
        args, kwargs = mock_redis.hset.call_args
        mapping = kwargs["mapping"]
        assert mapping["task_id"] == "test.task"
        assert mapping["last_job_id"] == "123"
        assert mapping["last_status"] == "running"

    @pytest.mark.asyncio
    async def test_mark_finished_success(self, registry, mock_redis, sample_task):
        mock_redis.hget.return_value = "0"  # consecutive_failures

        await registry.mark_finished(sample_task, status="success")

        mock_redis.hset.assert_called_once()
        mapping = mock_redis.hset.call_args[1]["mapping"]
        assert mapping["last_status"] == "success"
        assert mapping["consecutive_failures"] == "0"

    @pytest.mark.asyncio
    async def test_mark_finished_failed(self, registry, mock_redis, sample_task):
        mock_redis.hget.return_value = "1"  # previous failures

        await registry.mark_finished(sample_task, status="failed", error="Some error")

        mapping = mock_redis.hset.call_args[1]["mapping"]
        assert mapping["last_status"] == "failed"
        assert mapping["consecutive_failures"] == "2"
        assert mapping["last_error"] == "Some error"

    @pytest.mark.asyncio
    async def test_release_lock(self, registry, mock_redis):
        await registry.release_lock("test.task")
        mock_redis.delete.assert_called_with("worker:tasks:test.task:lock")

    @pytest.mark.asyncio
    async def test_schedule_next(self, registry, mock_redis, sample_task):
        mock_ctx = {"arq_service": AsyncMock()}
        mock_ctx["arq_service"].enqueue_job.return_value = MagicMock(job_id="next-123")

        job_id = await registry.schedule_next(mock_ctx, sample_task, function_name="some_func")

        assert job_id == "next-123"
        mock_ctx["arq_service"].enqueue_job.assert_called_once()
        # Should also call mark_finished
        assert mock_redis.hset.called

    @pytest.mark.asyncio
    async def test_schedule_next_no_arq(self, registry, sample_task):
        res = await registry.schedule_next({}, sample_task, function_name="func")
        assert res is None

    @pytest.mark.asyncio
    async def test_error_truncation(self, registry, mock_redis, sample_task):
        long_error = "A" * 2000
        await registry.mark_finished(sample_task, status="failed", error=long_error)

        mapping = mock_redis.hset.call_args[1]["mapping"]
        assert len(mapping["last_error"]) == 1000

        # Check event truncation too (300)
        event_call = mock_redis.lpush.call_args[0][1]
        event_data = json.loads(event_call)
        assert len(event_data["error"]) == 300
