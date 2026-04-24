# Telegram Bot (archived)

**Archived**: 2026-04-24
**Reason**: Switched to email-based admin notifications. The bot was disconnected from the notification chain and moved here to keep active codebase clean while preserving history.

## Original locations

- Source: `src/telegram_bot/` → `archive/telegram_bot/`
- Tests: `tests/telegram_bot/` → `archive/telegram_bot/tests/`

## How to restore

1. `git mv archive/telegram_bot/tests tests/telegram_bot`
2. `git mv archive/telegram_bot src/telegram_bot`
3. Restore `bot` service in `deploy/docker-compose.yml` (see git history before archive commit).
4. Restore env vars in `.env` / `.env.production`: `BOT_TOKEN`, `SUPERUSER_IDS`, `OWNER_IDS`, `BOT_DATA_MODE`, `TELEGRAM_ADMIN_CHANNEL_ID`, `TELEGRAM_NOTIFICATION_TOPIC_ID`, `TELEGRAM_TOPICS`, `BOT_API_KEY`.
5. In `src/lily_backend/features/booking/services/notifications.py` add `"telegram"` back into `channels` for booking events.
6. In `src/workers/notification_worker/tasks/notification_tasks.py` restore `_send_to_stream` body (see git history).
7. Surface `telegram_bot_username` in `src/lily_backend/system/admin/settings.py` fieldsets.

## What still references the bot after archiving

- `src/lily_backend/system/models/settings.py` — `telegram_bot_username` field kept as orphan (not removed via migration to avoid data loss).
- `src/workers/core/streams.py` — `BotEvents` constants kept as dead code (cheap, fast restore).
