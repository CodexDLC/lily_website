# 📂 Director Service

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

Coordinates navigation between features by managing FSM states and delegating to orchestrators.

**File:** `src/telegram_bot/services/director/director.py`

---

## 🎯 Purpose

When a user clicks a menu button or an orchestrator decides to navigate elsewhere, the Director:

1. Looks up the target orchestrator in `container.features`
2. Injects itself into the orchestrator (`set_director`)
3. Calls `orchestrator.handle_entry(user_id, payload)`

---

## 🏗️ Class: Director

### Constructor

| Parameter | Type | Description |
|:---|:---|:---|
| `container` | `BotContainer` | Access to `features` dict |
| `state` | `FSMContext` | Current user's FSM context |
| `user_id` | `int` | Telegram user ID |

Created **per-request** in handlers (not a singleton).

---

## 🔄 set_scene Flow

```text
set_scene(feature="bot_menu", payload=None)
│
├── 1. orchestrator = container.features.get("bot_menu")
│       └── If not found → log error, return None
├── 2. orchestrator.set_director(self)
└── 3. return await orchestrator.handle_entry(self.user_id, payload)
```

---

## 📜 OrchestratorProtocol

Every orchestrator accessed by Director must implement:

```python
@runtime_checkable
class OrchestratorProtocol(Protocol):
    async def render(self, payload: Any) -> Any: ...
    async def handle_entry(self, user_id: int, payload: Any = None) -> Any: ...
    def set_director(self, director: Any): ...
```

`BaseBotOrchestrator` satisfies this protocol automatically.

---

## 🔗 Usage in Handlers

```python
director = Director(container, state, user_id)
view_dto = await director.set_scene("target_feature", payload)
```

## 🔗 Usage in Orchestrators

Orchestrators can trigger navigation via `process_response`:

```python
response = CoreResponseDTO(
    header=ResponseHeader(next_state="other_feature"),
    payload=data
)
return await self.process_response(response)
# → BaseBotOrchestrator detects next_state ≠ current
# → Calls self.director.set_scene("other_feature", data)
```
