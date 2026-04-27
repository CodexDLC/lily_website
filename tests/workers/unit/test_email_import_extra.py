import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.workers.system_worker.tasks.email_import import _fetch_emails, _fetch_one, _extract_literal

@pytest.fixture
def mock_settings():
    s = MagicMock()
    s.imap_host = "imap.test.com"
    s.imap_user = "user"
    s.imap_password = "password"  # pragma: allowlist secret
    s.imap_port = 993
    s.imap_folder = "INBOX"
    s.email_import_batch_size = 10
    s.email_import_interval_sec = 60
    s.email_import_stale_after_sec = 120
    s.email_import_max_raw_bytes = 1024
    s.email_import_max_body_chars = 1000
    s.conversations_import_api_key = "test-key"  # pragma: allowlist secret
    return s

def test_fetch_emails_search_failed(mock_settings):
    with patch("imaplib.IMAP4_SSL") as mock_imap:
        mbox = mock_imap.return_value
        mbox.uid.return_value = ("NO", [b""])
        res = _fetch_emails(mock_settings)
        assert res == []

def test_fetch_one_failed(mock_settings):
    mbox = MagicMock()
    mbox.uid.return_value = ("NO", None)
    res = _fetch_one(mbox, "1", mock_settings)
    assert res is None

def test_fetch_emails_item_none(mock_settings):
    with patch("imaplib.IMAP4_SSL") as mock_imap:
        mbox = mock_imap.return_value
        mbox.uid.side_effect = [
            ("OK", [b"1"]), # search
            ("NO", None), # fetch in _fetch_one
        ]
        res = _fetch_emails(mock_settings)
        assert res == []

def test_extract_literal_none():
    assert _extract_literal(["not a tuple"]) is None

@pytest.mark.asyncio
async def test_import_emails_with_spam(mock_settings):
    from src.workers.system_worker.tasks.email_import import import_emails_task, NormalizedEmail
    ctx = {
        "settings": mock_settings,
        "heartbeat_registry": MagicMock(should_run=AsyncMock(return_value=True), mark_started=AsyncMock(), mark_finished=AsyncMock(), release_lock=AsyncMock()),
        "internal_api": MagicMock(post=AsyncMock()),
        "arq_service": MagicMock(enqueue_job=AsyncMock()),
    }

    spam_item = NormalizedEmail(
        uid="1", sender_name="S", sender_email="s@s.com", subject="S", body="B",
        text_truncated=False, oversized=False, spam=True, thread_key=None,
        message_id="id", in_reply_to="", references=[], attachments=[], raw_size=100
    )

    with patch("src.workers.system_worker.tasks.email_import._fetch_emails", return_value=[spam_item]):
        res = await import_emails_task(ctx)
        assert res["spam"] == 1
