from email.message import EmailMessage

import pytest

from workers.system_worker.config import WorkerSettings
from workers.system_worker.tasks.email_import import (
    _extract_text,
    _fetch_emails,
    _find_thread_key,
    _looks_like_spam,
    _normalize,
    _to_payload,
)


@pytest.fixture
def settings():
    return WorkerSettings()


class TestEmailImportLogic:
    def test_fetch_emails_skips_when_imap_disabled(self, monkeypatch):
        def fail_if_connected(*args, **kwargs):
            raise AssertionError("IMAP connection should not be attempted when settings are incomplete")

        monkeypatch.setattr("workers.system_worker.tasks.email_import.imaplib.IMAP4_SSL", fail_if_connected)
        settings = WorkerSettings(IMAP_HOST="", IMAP_USER="", IMAP_PASSWORD="")

        assert _fetch_emails(settings) == []

    def test_looks_like_spam(self):
        assert _looks_like_spam(sender_email="scam@scam.com", subject="Meta Business", body="Verify account") is True
        assert _looks_like_spam(sender_email="anna@lily.de", subject="Booking", body="Hello") is False

    def test_find_thread_key_from_header(self):
        msg = EmailMessage()
        msg["X-Lily-Thread-Key"] = "thread_key: ABC-123-XYZ-78900"
        key = _find_thread_key(msg, body="Some text", in_reply_to="", references=[])
        assert key == "ABC-123-XYZ-78900"

    def test_find_thread_key_from_body(self):
        msg = EmailMessage()
        body = "Please reply using thread_key: BODY-KEY-12345678"
        key = _find_thread_key(msg, body=body, in_reply_to="", references=[])
        assert key == "BODY-KEY-12345678"

    def test_extract_text_html(self):
        msg = EmailMessage()
        msg.set_content("<html><body><h1>Hello</h1><p>World</p></body></html>", subtype="html")
        text = _extract_text(msg)
        assert "Hello World" in text

    def test_extract_text_plain(self):
        msg = EmailMessage()
        msg.set_content("Just plain text")
        text = _extract_text(msg)
        assert text == "Just plain text"

    def test_normalize_basic(self, settings):
        msg = EmailMessage()
        msg["From"] = "Anna <anna@test.com>"
        msg["Subject"] = "Test Subject"
        msg["Message-ID"] = "msg-123"
        msg.set_content("Hello from worker")

        normalized = _normalize("uid-1", msg, settings, raw_size=100, oversized=False)

        assert normalized.uid == "uid-1"
        assert normalized.sender_name == "Anna"
        assert normalized.sender_email == "anna@test.com"
        assert normalized.subject == "Test Subject"
        assert normalized.body == "Hello from worker"
        assert normalized.message_id == "msg-123"

    def test_to_payload(self, settings):
        msg = EmailMessage()
        msg["From"] = "anna@test.com"
        msg.set_content("Body")
        item = _normalize("1", msg, settings, raw_size=10, oversized=False)

        payload = _to_payload(item)
        assert payload["sender_email"] == "anna@test.com"
        assert payload["body"] == "Body"
        assert "thread_key" in payload
