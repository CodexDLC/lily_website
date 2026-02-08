# 📂 ViewSender Service

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

Smart message sender that manages the bot's UI messages (send, edit, or delete).

**File:** `src/telegram_bot/services/sender/view_sender.py`

---

## 🎯 Purpose

The bot maintains up to two persistent messages per user:

- **Menu message** — dashboard / navigation (inline keyboard)
- **Content message** — feature-specific content

ViewSender ensures these messages are correctly updated (edited) rather than duplicated.

---

## 🏗️ Class: ViewSender

```text
BaseUIService
  └── ViewSender
```

### Constructor

| Parameter | Type | Description |
|:---|:---|:---|
| `bot` | `Bot` | aiogram Bot instance |
| `state` | `FSMContext` | Current FSM context |
| `old_state_data` | `dict` | Previous state data (for cleanup) |
| `user_id` | `int` | Telegram user ID |

---

## 🔄 Send Flow

```text
send(unified_view_dto: UnifiedViewDTO)
│
├── 1. If clean_history=True:
│       └── Delete previous menu + content messages
├── 2. Process menu message:
│       ├── If previous menu exists → edit_text
│       └── If no previous → send_message
├── 3. Process content message:
│       ├── If previous content exists → edit_text
│       └── If no previous → send_message
└── 4. Save new message IDs in FSM state data
```

---

## 📦 Message Tracking

Message IDs are stored in FSM state data under `KEY_UI_COORDS`:

```python
state_data = {
    "ui_coords": {
        "menu_message_id": 12345,
        "content_message_id": 12346,
    }
}
```

This allows ViewSender to find and edit/delete previous messages on the next interaction.

---

## 🗺️ Input DTOs

### UnifiedViewDTO

| Field | Type | Description |
|:---|:---|:---|
| `menu` | `ViewResultDTO \| None` | Menu message (text + keyboard) |
| `content` | `ViewResultDTO \| None` | Content message (text + keyboard) |
| `clean_history` | `bool` | Delete all previous messages before sending |

### ViewResultDTO

| Field | Type | Description |
|:---|:---|:---|
| `text` | `str` | Message text (HTML) |
| `kb` | `InlineKeyboardMarkup \| None` | Inline keyboard |
