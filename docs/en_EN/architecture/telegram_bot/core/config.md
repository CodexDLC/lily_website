# 📜 Config (Environment Settings)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Pydantic-based settings that read from `.env` file.

**File:** `src/telegram_bot/core/config.py`

---

## 🏗️ Inheritance

```text
CommonSettings (shared/core/config.py)
  └── BotSettings (telegram_bot/core/config.py)
```

`CommonSettings` provides shared fields (Redis, debug mode, log paths). `BotSettings` adds bot-specific fields.

---

## 📋 Environment Variables

| Variable | Type | Default | Description |
|:---|:---|:---|:---|
| `BOT_TOKEN` | `str` | *required* | Telegram Bot API token |
| `BUG_REPORT_CHANNEL_ID` | `int \| None` | `None` | Channel for error reports |
| `SUPERUSER_IDS` | `str` | `""` | Comma-separated developer Telegram IDs |
| `OWNER_IDS` | `str` | `""` | Comma-separated business owner IDs |
| `BACKEND_API_URL` | `str` | `http://localhost:8000` | FastAPI backend URL |
| `BACKEND_API_KEY` | `str \| None` | `None` | API authentication key |
| `BACKEND_API_TIMEOUT` | `float` | `10.0` | HTTP request timeout (seconds) |

Plus inherited from `CommonSettings`: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `DEBUG`.

---

## 🔐 RBAC Properties

| Property | Returns | Description |
|:---|:---|:---|
| `superuser_ids_list` | `list[int]` | Parsed developer IDs |
| `owner_ids_list` | `list[int]` | Parsed business owner IDs |
| `roles` | `dict[str, list[int]]` | Combined role map for access checks |

### Role Hierarchy

```text
superuser → Full access (developers, tech support)
owner     → Admin access (business owners) + superusers
admin     → Alias for owner (backward compatibility)
```

Superusers automatically have owner-level access.
