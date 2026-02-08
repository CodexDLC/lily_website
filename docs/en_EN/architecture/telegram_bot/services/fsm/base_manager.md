# 📜 BaseStateManager

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../README.md)

Draft storage utility for features that need to persist temporary data across FSM interactions.

**File:** `src/telegram_bot/services/fsm/base_manager.py`

---

## 🎯 Purpose

When a feature has multi-step forms (e.g., create profile → enter name → enter bio → confirm), each step needs to store intermediate data. `BaseStateManager` provides an isolated namespace in FSM state data.

---

## 🏗️ Class: BaseStateManager

### Constructor

| Parameter | Type | Description |
|:---|:---|:---|
| `state` | `FSMContext` | User's FSM context |
| `feature_key` | `str` | Unique key for namespace isolation |

---

## 📋 Methods

| Method | Description |
|:---|:---|
| `get_payload()` | Get full draft dictionary |
| `update(**kwargs)` | Merge values into draft |
| `clear()` | Remove all draft data |
| `set_value(key, value)` | Set a single field |
| `get_value(key, default)` | Get a single field |

---

## 🔧 Storage Format

Data is stored under `draft:{feature_key}` in FSM state:

```python
# FSM state_data after manager.update(name="John", age=25):
{
    "draft:my_feature": {
        "name": "John",
        "age": 25
    },
    "ui_coords": { ... }  # Other state data is untouched
}
```

Each feature's data is fully isolated from other features.
