from __future__ import annotations

import asyncio
import contextlib
import imaplib
import re
from dataclasses import dataclass
from datetime import timedelta
from email import message_from_bytes
from email.policy import default
from email.utils import getaddresses, parseaddr
from html import unescape
from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.workers.core.heartbeat import HeartbeatTask, WorkerHeartbeatRegistry

if TYPE_CHECKING:
    from email.message import Message

    from src.workers.core.internal_api import InternalApiClient
    from src.workers.system_worker.config import WorkerSettings

TASK_ID = "conversations.import"
QUEUE_NAME = "system"
_SIZE_RE = re.compile(rb"RFC822\.SIZE\s+(\d+)", re.IGNORECASE)
_THREAD_KEY_RE = re.compile(r"(?:thread_key|thread|reply_match_token)[=:]\s*([A-Za-z0-9_\-]{16,128})", re.I)


@dataclass
class NormalizedEmail:
    uid: str
    sender_name: str
    sender_email: str
    subject: str
    body: str
    text_truncated: bool
    oversized: bool
    spam: bool
    thread_key: str | None
    message_id: str
    in_reply_to: str
    references: list[str]
    attachments: list[dict[str, Any]]
    raw_size: int | None


async def import_emails_task(ctx: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    settings = cast("WorkerSettings", ctx["settings"])
    registry = cast("WorkerHeartbeatRegistry", ctx["heartbeat_registry"])
    task = HeartbeatTask(
        task_id=TASK_ID,
        domain="conversations",
        queue_name=QUEUE_NAME,
        expected_interval_sec=settings.email_import_interval_sec,
        stale_after_sec=settings.email_import_stale_after_sec,
    )
    if not await registry.should_run(task.task_id, lock_ttl_sec=task.stale_after_sec):
        await registry.mark_finished(task, status="skipped")
        return None

    try:
        await registry.mark_started(task, job_id=str(ctx.get("job_id", "")))
        emails = await asyncio.to_thread(_fetch_emails, settings)
        client = cast("InternalApiClient", ctx["internal_api"])
        imported = 0
        spam = 0
        oversized = 0
        for item in emails:
            if item.spam:
                spam += 1
            if item.oversized:
                oversized += 1
            await client.post(
                "/v1/conversations/import-email",
                scope=TASK_ID,
                token=settings.conversations_import_api_key,
                json=_to_payload(item),
            )
            imported += 1
        await _schedule_next(ctx, task)
        await registry.mark_finished(task, status="success")
        return {"imported": imported, "spam": spam, "oversized": oversized}
    except Exception as exc:
        log.exception("import_emails_task failed")
        await registry.mark_finished(task, status="failed", error=str(exc))
        raise
    finally:
        await registry.release_lock(task.task_id)


def _fetch_emails(settings: WorkerSettings) -> list[NormalizedEmail]:
    if not settings.imap_host or not settings.imap_user or not settings.imap_password:
        log.info("IMAP import skipped: IMAP_HOST/IMAP_USER/IMAP_PASSWORD are incomplete.")
        return []

    mailbox = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    try:
        mailbox.login(settings.imap_user, settings.imap_password)
        mailbox.select(settings.imap_folder)
        status, data = mailbox.uid("search", "UNSEEN")
        if status != "OK" or not data:
            return []
        uids = data[0].split()[: settings.email_import_batch_size]
        normalized = []
        for uid_bytes in uids:
            uid = uid_bytes.decode()
            item = _fetch_one(mailbox, uid, settings)
            if item is None:
                continue
            normalized.append(item)
            if item.spam:
                _move_message(mailbox, uid, settings.imap_spam_folder)
            else:
                _move_message(mailbox, uid, settings.imap_archive_folder)
        mailbox.expunge()
        return normalized
    finally:
        with contextlib.suppress(imaplib.IMAP4.error):
            mailbox.logout()


def _fetch_one(mailbox: imaplib.IMAP4_SSL, uid: str, settings: WorkerSettings) -> NormalizedEmail | None:
    status, meta = mailbox.uid("fetch", uid, "(RFC822.SIZE BODY.PEEK[HEADER])")
    if status != "OK":
        return None
    raw_size = _extract_size(meta)
    header_bytes = _extract_literal(meta) or b""
    oversized = raw_size is not None and raw_size > settings.email_import_max_raw_bytes
    raw_message = header_bytes
    if not oversized:
        status, raw = mailbox.uid("fetch", uid, "(BODY.PEEK[])")
        if status == "OK":
            raw_message = _extract_literal(raw) or header_bytes
    msg = message_from_bytes(raw_message, policy=default)
    return _normalize(uid, msg, settings, raw_size=raw_size, oversized=oversized)


def _normalize(
    uid: str,
    msg: Message,
    settings: WorkerSettings,
    *,
    raw_size: int | None,
    oversized: bool,
) -> NormalizedEmail:
    msg_any = cast("Any", msg)
    sender_name, sender_email = parseaddr(str(msg.get("From", "")))
    subject = str(msg.get("Subject", ""))
    message_id = str(msg.get("Message-ID", "")).strip()
    in_reply_to = str(msg.get("In-Reply-To", "")).strip()
    references = [addr for _name, addr in getaddresses([str(msg.get("References", ""))]) if addr]
    body = "" if oversized else _extract_text(msg_any)
    text_truncated = len(body) > settings.email_import_max_body_chars
    if text_truncated:
        body = body[: settings.email_import_max_body_chars]
    attachments = [] if oversized else _attachments(msg_any)
    thread_key = _find_thread_key(msg_any, body, in_reply_to, references)
    spam = _looks_like_spam(sender_email=sender_email, subject=subject, body=body)
    return NormalizedEmail(
        uid=uid,
        sender_name=sender_name,
        sender_email=sender_email or "unknown@example.invalid",
        subject=subject,
        body=body,
        text_truncated=text_truncated,
        oversized=oversized,
        spam=spam,
        thread_key=thread_key,
        message_id=message_id,
        in_reply_to=in_reply_to,
        references=references,
        attachments=attachments,
        raw_size=raw_size,
    )


def _extract_text(msg: Any) -> str:
    try:
        body_part = msg.get_body(preferencelist=("plain", "html"))
    except (AttributeError, TypeError):
        body_part = None
    if body_part is None:
        return ""
    content = body_part.get_content()
    if body_part.get_content_type() == "text/html":
        content = re.sub(r"<(script|style).*?</\1>", "", content, flags=re.I | re.S)
        content = re.sub(r"<[^>]+>", " ", content)
        content = unescape(content)
    return " ".join(str(content).split())


def _attachments(msg: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for part in msg.walk():
        if part.is_multipart():
            continue
        disposition = part.get_content_disposition()
        filename = part.get_filename("")
        if disposition != "attachment" and not filename:
            continue
        payload = part.get_payload(decode=True)
        results.append(
            {
                "filename": filename or "",
                "content_type": part.get_content_type(),
                "size": len(payload) if payload is not None else None,
                "storage_url": None,
            }
        )
    return results


def _find_thread_key(msg: Any, body: str, in_reply_to: str, references: list[str]) -> str | None:
    headers = " ".join(
        str(msg.get(name, ""))
        for name in ("X-Lily-Thread-Key", "X-Thread-Key", "Thread-Index", "In-Reply-To", "References")
    )
    for source in (headers, body, in_reply_to, " ".join(references)):
        match = _THREAD_KEY_RE.search(source)
        if match:
            return match.group(1)
    for token in [in_reply_to, *references]:
        cleaned = token.strip("<> ")
        if 16 <= len(cleaned) <= 128 and re.fullmatch(r"[A-Za-z0-9_\-]+", cleaned):
            return cleaned
    return None


def _looks_like_spam(*, sender_email: str, subject: str, body: str) -> bool:
    text = f"{sender_email} {subject} {body}".lower()
    suspicious = [
        "facebook business account",
        "meta business",
        "verify your account",
        "crypto",
        "wallet",
        "casino",
        "loan approved",
    ]
    return any(marker in text for marker in suspicious)


def _extract_size(items: list[Any]) -> int | None:
    joined = b" ".join(item if isinstance(item, bytes) else b"" for item in items)
    match = _SIZE_RE.search(joined)
    return int(match.group(1)) if match else None


def _extract_literal(items: list[Any]) -> bytes | None:
    for item in items:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            return item[1]
    return None


def _move_message(mailbox: imaplib.IMAP4_SSL, uid: str, folder: str) -> None:
    if not folder:
        return
    try:
        mailbox.uid("copy", uid, folder)
        mailbox.uid("store", uid, "+FLAGS", r"(\Deleted)")
    except imaplib.IMAP4.error as exc:
        log.warning(f"Could not move imported email uid={uid} to folder={folder}: {exc}")


def _to_payload(item: NormalizedEmail) -> dict[str, Any]:
    return {
        "sender_name": item.sender_name,
        "sender_email": item.sender_email,
        "subject": item.subject,
        "body": item.body,
        "text_truncated": item.text_truncated,
        "oversized": item.oversized,
        "spam": item.spam,
        "thread_key": item.thread_key,
        "message_id": item.message_id,
        "in_reply_to": item.in_reply_to,
        "references": item.references,
        "attachments": item.attachments,
        "raw_size": item.raw_size,
    }


async def _schedule_next(ctx: dict[str, Any], task: HeartbeatTask) -> None:
    arq_service = ctx.get("arq_service")
    if not arq_service:
        return
    await arq_service.enqueue_job(
        "import_emails_task",
        _defer_by=timedelta(seconds=task.expected_interval_sec),
        _queue_name=task.queue_name,
        _job_id=f"{task.task_id}:next",
    )
