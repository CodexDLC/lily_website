from email.message import EmailMessage
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workers.system_worker.config import WorkerSettings
from src.workers.system_worker.tasks.email_import import (
    _extract_text,
    _fetch_emails,
    _fetch_one,
    _find_thread_key,
    _looks_like_spam,
    _move_message,
    _schedule_next,
    import_emails_task,
)


@pytest.fixture
def settings():
    return WorkerSettings()


@pytest.fixture
def ctx(settings):
    ctx_obj = {
        "settings": settings,
        "heartbeat_registry": AsyncMock(),
        "internal_api": AsyncMock(),
        "arq_service": AsyncMock(),
        "job_id": "test_job",
    }
    # Fix: should_run is an async method
    ctx_obj["heartbeat_registry"].should_run = AsyncMock(return_value=True)
    ctx_obj["heartbeat_registry"].mark_started = AsyncMock()
    ctx_obj["heartbeat_registry"].mark_finished = AsyncMock()
    ctx_obj["heartbeat_registry"].release_lock = AsyncMock()
    return ctx_obj


class TestEmailImportLogic:
    def test_fetch_emails_skips_when_imap_disabled(self):
        settings = WorkerSettings(imap_host="", imap_user="", imap_password="")
        assert _fetch_emails(settings) == []

    @patch("src.workers.system_worker.tasks.email_import.imaplib.IMAP4_SSL")
    def test_fetch_emails_success(self, mock_imap, settings):
        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn

        settings.imap_host = "imap.test.com"
        settings.imap_user = "user"
        settings.imap_password = "pwd"  # pragma: allowlist secret

        # Sequence:
        # 1. search -> "1"
        # 2. fetch(1) meta -> size 100 via RFC822.SIZE
        # 3. fetch(1) body -> payload
        # 4. copy(1) -> OK
        # 5. store(1) -> OK
        mock_conn.uid.side_effect = [
            ("OK", [b"1"]),  # search
            ("OK", [b"RFC822.SIZE 100", (None, b"From: anna@test.com\r\nSubject: Test\r\n\r\n")]),  # fetch meta
            ("OK", [(None, b"From: anna@test.com\r\nSubject: Test\r\n\r\nBody")]),  # fetch body
            ("OK", [b"OK"]),  # copy
            ("OK", [b"OK"]),  # store
        ]

        emails = _fetch_emails(settings)
        assert len(emails) == 1
        assert emails[0].sender_email == "anna@test.com"

    @patch("src.workers.system_worker.tasks.email_import.imaplib.IMAP4_SSL")
    def test_fetch_one_oversized(self, mock_imap, settings):
        mock_conn = MagicMock()
        # RFC822.SIZE 9999999
        mock_conn.uid.return_value = ("OK", [b"RFC822.SIZE 9999999", (None, b"From: a@b.c\r\n\r\n")])

        settings.email_import_max_raw_bytes = 1000
        item = _fetch_one(mock_conn, "1", settings)
        assert item.oversized is True
        assert item.body == ""

    def test_looks_like_spam(self):
        assert _looks_like_spam(sender_email="scam@scam.com", subject="Meta Business", body="Verify account") is True
        assert _looks_like_spam(sender_email="anna@lily.de", subject="Booking", body="Hello") is False

    def test_find_thread_key_logic(self):
        msg = EmailMessage()
        # Must match re: (?:thread_key|thread|reply_match_token)[=:]\s*([A-Za-z0-9_\-]{16,128})
        valid_key = "ABC-123-XYZ-789-DEF-456"  # > 16 chars
        msg["X-Lily-Thread-Key"] = f"thread_key: {valid_key}"
        assert _find_thread_key(msg, "", "", []) == valid_key

        # Body match
        assert _find_thread_key(EmailMessage(), f"thread={valid_key}", "", []) == valid_key

        # Direct token match (16-128 chars, no prefix)
        token = "DirectToken1234567890"
        assert _find_thread_key(EmailMessage(), "", f"<{token}>", []) == token

    def test_extract_text_handling(self):
        msg = EmailMessage()
        msg.set_content("<html><body><h1>Hi</h1></body></html>", subtype="html")
        assert "Hi" in _extract_text(msg)

        msg = EmailMessage()
        msg.set_content("Plain")
        assert _extract_text(msg) == "Plain"

    @pytest.mark.asyncio
    async def test_import_emails_task_skipped(self, ctx):
        ctx["heartbeat_registry"].should_run.return_value = False
        res = await import_emails_task(ctx)
        assert res is None

    @pytest.mark.asyncio
    async def test_import_emails_task_success(self, ctx):
        ctx["heartbeat_registry"].should_run.return_value = True

        with patch("src.workers.system_worker.tasks.email_import._fetch_emails") as mock_fetch:
            mock_fetch.return_value = [MagicMock(spam=False, oversized=False), MagicMock(spam=True, oversized=False)]
            res = await import_emails_task(ctx)
            assert res["imported"] == 2
            assert res["spam"] == 1
            assert ctx["internal_api"].post.call_count == 2

    @pytest.mark.asyncio
    async def test_import_emails_task_failure(self, ctx):
        ctx["heartbeat_registry"].should_run.return_value = True
        # Note: import_emails_task re-raises, but we need to catch it to avoid test failure
        with patch("src.workers.system_worker.tasks.email_import._fetch_emails", side_effect=Exception("Crash")):
            with pytest.raises(Exception, match="Crash"):
                await import_emails_task(ctx)
            args, kwargs = ctx["heartbeat_registry"].mark_finished.call_args
            assert kwargs["status"] == "failed"
            assert kwargs["error"] == "Crash"

    def test_move_message_error_handling(self):
        mock_conn = MagicMock()
        import imaplib

        mock_conn.uid.side_effect = imaplib.IMAP4.error("imap failure")
        _move_message(mock_conn, "1", "Folder")

    @pytest.mark.asyncio
    async def test_schedule_next(self, ctx):
        # We need a HeartbeatTask object for schedule_next
        mock_task = MagicMock()
        mock_task.task_id = "t"
        mock_task.expected_interval_sec = 60
        mock_task.queue_name = "q"
        await _schedule_next(ctx, mock_task)
        ctx["arq_service"].enqueue_job.assert_called_once()
