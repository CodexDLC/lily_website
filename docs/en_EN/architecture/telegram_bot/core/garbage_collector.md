# 📜 Garbage Collector

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Dynamic system that automatically deletes unwanted text messages in specific FSM states.

**File:** `src/telegram_bot/core/garbage_collector.py`

---

## 🎯 Problem

When a bot shows inline-keyboard screens, users sometimes type random text. This text clutters the chat. The garbage collector detects and deletes such messages in registered "garbage" states.

---

## 🏗️ Components

### GarbageStateRegistry (Class-level registry)

A global set that tracks which FSM states should trigger text deletion.

```python
GarbageStateRegistry.register(MyFeatureStates)  # Register all states
GarbageStateRegistry.is_garbage("MyFeatureStates:main")  # Check state
```

### IsGarbageStateFilter (aiogram Filter)

Custom aiogram filter used by `common_fsm_handlers.py` router:

```python
@router.message(F.text, IsGarbageStateFilter())
async def delete_garbage_text(message: Message):
    await message.delete()
```

---

## 🔄 Registration Flow

```text
1. BotContainer.__init__()
2.   → discovery_service.discover_all()
3.     → For each feature in INSTALLED_FEATURES:
4.       → Load feature_setting.py
5.       → If GARBAGE_COLLECT = True → register STATES
6.       → If GARBAGE_STATES = [...] → register explicit list
7. GarbageStateRegistry now contains all "garbage" states
```

---

## ⚙️ Feature Configuration

In `feature_setting.py`:

```python
# Option 1: Auto-register all states
GARBAGE_COLLECT = True
STATES = MyFeatureStates  # All states in this group become "garbage"

# Option 2: Explicit list
GARBAGE_STATES = [MyFeatureStates.editing, MyFeatureStates.viewing]

# Option 3: Disabled
GARBAGE_COLLECT = False
```

---

## 📍 Router Placement

The garbage collector router is always registered **last** in the router chain (via `routers.py`), so it only catches messages that no other handler matched.
