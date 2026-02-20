# 🤖 Telegram Bot — Basic Flow

> Quick understanding of **what happens when a user clicks a button**.
> For deep dive into each component — see documentation links at the end.

---

## 1️⃣ Bot Startup (`app_telegram.py`)

```
BotSettings (env vars)
    → Redis client
    → BotContainer          ← assembles all services and orchestrators
    → build_bot()           ← creates Bot + Dispatcher + RedisStorage (FSM)
    → attach middlewares    ← order matters (see §3)
    → build_main_router()   ← auto-scanning handlers from INSTALLED_FEATURES
    → stream_processor.start_listening()   ← background Redis Stream listener
    → dp.start_polling(bot)
```

📄 Details: [app_telegram.md](../../docs/en_EN/architecture/telegram_bot/app_telegram.md)

---

## 2️⃣ What happens on every Update from Telegram

```
Telegram API
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    MIDDLEWARE CHAIN                          │
│                                                             │
│  1. UserValidationMiddleware  → is there a from_user?       │
│     ✗ no user → return None (ignore)                        │
│     ✓ user → data["user"] = user                            │
│                                                             │
│  2. ThrottlingMiddleware      → flood protection (Redis TTL)│
│     ✗ throttle:{user_id} key exists → alert + None          │
│     ✓ ok → set key with TTL=1.0s                            │
│                                                             │
│  3. SecurityMiddleware        → FSM session check           │
│     ✗ user_id in FSM ≠ from_user.id → alert + None          │
│     ✓ ok → continue                                         │
│                                                             │
│  4. ContainerMiddleware       → DI                          │
│     data["container"] = BotContainer                        │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      HANDLER (features/)                     │
│                                                             │
│  Receives: event, data["user"], data["container"]           │
│                                                             │
│  handler(callback, container, state):                       │
│      orchestrator = container.bot_menu   # or other         │
│      view = await orchestrator.render(payload)              │
│      await container.view_sender.send(view)                 │
└─────────────────────────────────────────────────────────────┘
```

📄 Middlewares: [middlewares/README.md](../../docs/en_EN/architecture/telegram_bot/middlewares/README.md)

---

## 3️⃣ Inside Handler — Orchestrator Flow

```
Handler
    │
    ▼
BaseBotOrchestrator
    │
    ├─ handle_entry(user_id, payload)    ← cold start (data loading)
    │       └─ calls render()
    │
    └─ render(payload) → UnifiedViewDTO
            │
            ├─ if payload = CoreResponseDTO from backend:
            │       process_response()
            │           └─ if response.next_state ≠ expected_state
            │                   → Director.set_scene(feature, payload)  # scene change!
            │
            └─ render_content(payload)  ← implemented in each feature
                    └─ returns ViewResultDTO (text + keyboard)
```

📄 Details: [services/base/base_orchestrator.md](../../docs/en_EN/architecture/telegram_bot/services/base/base_orchestrator.md)

---

## 4️⃣ Director — Switching between features

```
Director.set_scene("bot_menu", payload)
    │
    ├─ orchestrator = container.features["bot_menu"]
    ├─ orchestrator.set_director(self)
    └─ view = await orchestrator.handle_entry(user_id, payload)
```

> Director is the "stage manager". It knows about all features (via `BotContainer`)
> and switches scenes when the backend returns `next_state`.

📄 Details: [services/director/director.md](../../docs/en_EN/architecture/telegram_bot/services/director/director.md)

---

## 5️⃣ ViewSender — Sending/Editing UI

```
ViewSender.send(UnifiedViewDTO)
    │
    ├─ get_coords() from Redis        ← menu_msg_id, content_msg_id
    │
    ├─ if clean_history → delete old messages + clear coords
    │
    ├─ _process_message(view.menu)
    │       └─ edit if msg_id exists, otherwise send_message
    │
    └─ _process_message(view.content)
            └─ edit if msg_id exists, otherwise send_message
    │
    └─ update_coords() in Redis     ← save new message IDs
```

> The bot **does not flood with new messages** — it edits existing ones.
> IDs are stored in Redis to know what to edit.

📄 Details: [services/sender/view_sender.md](../../docs/en_EN/architecture/telegram_bot/services/sender/view_sender.md)

---

## 6️⃣ Redis Stream Flow (background events from backend)

```
Django Backend
    → writes event to Redis Stream
    │
    ▼
RedisStreamProcessor (polling loop, every 1.0s)
    → reads batch of messages
    → callback → BotRedisDispatcher
    → routing → Feature Redis Handler (INSTALLED_REDIS_FEATURES)
    → ack_event() ← confirm processing
```

📄 Details: [services/redis/stream_processor.md](../../docs/en_EN/architecture/telegram_bot/services/redis/stream_processor.md)

---

## 7️⃣ How to register a new feature

```python
# core/settings.py
INSTALLED_FEATURES = [
    ...,
    "features.my_feature",          # if there are Telegram handlers
]
INSTALLED_REDIS_FEATURES = [
    ...,
    "features.redis.my_feature",    # if listening to Redis Stream
]
```

A feature must have:
- `handlers.py` with `router = Router()` (for Telegram) or `redis_router` (for Redis)
- `feature_setting.py` with optional `MENU_CONFIG`, `GARBAGE_STATES`
- `create_orchestrator(container)` — orchestrator factory

📄 Details: [core/settings.md](../../docs/en_EN/architecture/telegram_bot/core/settings.md) | [services/feature_discovery/service.md](../../docs/en_EN/architecture/telegram_bot/services/feature_discovery/service.md)

---

## 📚 Documentation Map

| Layer | Document |
|---|---|
| Entry Point | [app_telegram.md](../../docs/en_EN/architecture/telegram_bot/app_telegram.md) |
| Configuration | [core/config.md](../../docs/en_EN/architecture/telegram_bot/core/config.md) |
| DI Container | [core/container.md](../../docs/en_EN/architecture/telegram_bot/core/container.md) |
| Middlewares | [middlewares/README.md](../../docs/en_EN/architecture/telegram_bot/middlewares/README.md) |
| Base Orchestrator | [services/base/base_orchestrator.md](../../docs/en_EN/architecture/telegram_bot/services/base/base_orchestrator.md) |
| Director | [services/director/director.md](../../docs/en_EN/architecture/telegram_bot/services/director/director.md) |
| ViewSender | [services/sender/view_sender.md](../../docs/en_EN/architecture/telegram_bot/services/sender/view_sender.md) |
| FSM Manager | [services/fsm/base_manager.md](../../docs/en_EN/architecture/telegram_bot/services/fsm/base_manager.md) |
| Redis Stream | [services/redis/stream_processor.md](../../docs/en_EN/architecture/telegram_bot/services/redis/stream_processor.md) |
| Auto-discovery | [services/feature_discovery/service.md](../../docs/en_EN/architecture/telegram_bot/services/feature_discovery/service.md) |
| Entire Telegram Bot | [telegram_bot/README.md](../../docs/en_EN/architecture/telegram_bot/README.md) |

---

> 🤖 **For AI Assistants / Developers:**
> Please read the **[AI Context & Custom Patterns](./ai_context.md)** document before modifying the code. This bot uses a custom Enterprise-grade architecture that significantly differs from standard `aiogram` tutorials (strict DI, isolated Drafts, Sender managers, dual Redis/Telegram feature types).
