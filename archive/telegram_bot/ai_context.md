# 🤖 AI Context & Custom Patterns

> **Attention for AI Assistants!**
> The architecture of this Telegram bot **differs significantly** from standard `aiogram` tutorials. It uses a custom Enterprise pattern. Be sure to read this document before making any changes.

---

## 1. Differences from Industry Standard (aiogram)

| Standard aiogram approach | Custom Pattern (used here) |
| :--- | :--- |
| Business logic directly in Telegram handlers. | **Handlers are completely empty**. They only intercept the update and call the required `Orchestrator` from the container. |
| Global variables or `Bot`/`db` in closures. | Strict **Dependency Injection**. Everything resides in `BotContainer`, which is passed via `ContainerMiddleware` into `data["container"]`. |
| Routers are imported and connected manually in `main.py`. | **Auto-discovery**. All features are listed as strings in `core/settings.py` (`INSTALLED_FEATURES`), and `FeatureDiscoveryService` automatically finds and assembles them. |
| `bot.send_message` for every app action (clutters history). | **Single Message Pattern (ViewSender)**. The bot stores message coordinates (`menu` and `content`) in Redis and *edits* them so the interface doesn't scroll up. |
| FSM states are flat, data is stored directly in `state.update_data(key=val)`. | Isolated **Draft Managers**. Each feature has its own `BaseStateManager`, data is stored in the `draft:{feature_name}` namespace. |

---

## 2. Deep Dive into Key Patterns

### 🎯 2.1 The Orchestrator Pattern (Separation of Logic and UI)

Instead of mixing Telegram API, database, and business logic into one pile, there is a strict separate cycle:

1. **Telegram Handler** catches the update.
2. Retrieves the **Orchestrator** from the `container`.
3. Calls `await orchestrator.render(payload)`.
4. Orchestrator consults **Contracts** (data providers) to fetch logic.
5. Orchestrator passes raw data to the **UI** layer (`render_content`), which returns `ViewResultDTO` (text + buttons).
6. Orchestrator wraps this into `UnifiedViewDTO` and returns it to the handler.
7. Handler passes the DTO to `ViewSender` for rendering.

**Why this is done:** So that business logic knows nothing about Telegram. The orchestrator operates with DTOs and interfaces, not `Message` or `CallbackQuery`.

### 🔀 2.2 The Director Pattern (Routing)

**Problem:** How can Feature A tell the bot to "show Feature B" if they are isolated and don't know about each other?
**Solution:** `Director`.

If the backend (responding to a user action) returns a `CoreResponseDTO` with a `next_state="bot_menu"` field, the current Orchestrator sees that `next_state` does not match its expectations and calls:
```python
await self.director.set_scene(feature="bot_menu", payload=response.payload)
```
The Director automatically finds the required orchestrator in the container and calls its entry point (`handle_entry`).

### 📦 2.3 Feature Plugin System & Auto-Discovery

The system works like plugins (inspired by Django's `INSTALLED_APPS`).
The `src/telegram_bot/core/settings.py` file is the center of everything.

At startup, `FeatureDiscoveryService`:
1. Reads `INSTALLED_FEATURES`.
2. Looks for `feature_setting.py` in them.
3. Registers states in the FSM Garbage Collector.
4. Calls the `create_orchestrator` factory, creating instances and placing them in `BotContainer.features`.
5. Looks for `MENU_CONFIG` to display buttons on the main Dashboard.
6. Extracts routers from `handlers.py` and assembles them into `main_router`.

### ✉️ 2.4 ViewSender & Redis UI Coordinates

The most non-standard pattern for UI.
The bot behaves like a **Single Page Application** inside Telegram.

- When a View needs to be sent, `ViewSender` accesses its Redis (`SenderManager`).
- Looks for `menu_msg_id` and `content_msg_id` for the current `user_id` / `chat_id`.
- If found — performs `bot.edit_message_text`.
- If not found (first run or `clean_history` feature triggered) — performs `bot.send_message` and writes new IDs back to Redis.

*AI Note: Never use `bot.send_message` directly in handlers (except for critical errors, bypassing everything). Always return `UnifiedViewDTO` and send via `container.view_sender.send()`.*

### 🗑️ 2.5 Garbage Collector & `IsGarbageStateFilter`

To prevent the user from breaking a complex FSM by sending text where only an inline button click is expected (which breaks the "SPA" interface):
1. `GARBAGE_COLLECT = True` is specified in `feature_setting.py`.
2. All states of this feature are added to the `GarbageStateRegistry`.
3. Middleware or a general handler `common_fsm_handlers.py` catches any text if the user is in these states and silently performs `await message.delete()`. The scene remains intact.

### 📡 2.6 Dual Feature System: Telegram vs Redis

The bot has **two completely different mechanisms** for processing events that live in parallel.

#### A. Telegram Features (`INSTALLED_FEATURES`)
- Trigger: User input (text, buttons) in Telegram.
- Entry: `src.telegram_bot...handlers` -> `router: aiogram.Router`
- Logic: FSM State, `ViewSender` updates the existing interface.

#### B. Redis Features (`INSTALLED_REDIS_FEATURES`)
- Trigger: Asynchronous event from the Django backend (e.g., "new request created").
- Mechanism: `RedisStreamProcessor` worker (custom long-polling) reads the `bot_events` stream.
- Wrapper: `BotRedisDispatcher` emulates aiogram, allowing to write `@redis_router.message("new_appointment")`.
- Specifics: They have **no FSM context**, **no User object**. They receive raw JSON payload from the backend.
- Fault Tolerance: If a Redis handler fails, `BotRedisDispatcher` schedules a task in the **ARQ pool** to delay processing by 60 seconds (Retry mechanism).

---

## 📝 Checklist for AI when generating code

1. **No logic in `handlers.py`**. Call the orchestrator.
2. **Do not use `bot.send_message()`**. Form `ViewResultDTO` and give it to the orchestrator -> `UnifiedViewDTO`.
3. **Store temporary feature data** by inheriting from `BaseStateManager`, not via flat `state.update_data()`.
4. If creating a new feature — **don't forget** to add the folder, `feature_setting.py`, `create_orchestrator` factory, and register the path in `core/settings.py`.
5. **Navigation** between features — only via returning `response.header.next_state` or direct call to `director.set_scene()`, do not hardcode transitions within the UI layer.
