# 📜 Global States

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Global FSM state definitions shared across the bot.

**File:** `src/telegram_bot/resources/states.py`

---

## 📋 Contents

| Name | Type | Description |
|:---|:---|:---|
| `GARBAGE_TEXT_STATES` | `list` | Legacy list of garbage states (now managed dynamically by `GarbageStateRegistry`) |

---

## 📝 Note

In the current architecture, garbage state registration is handled automatically by `FeatureDiscoveryService` through `feature_setting.py` in each feature. The global `states.py` is kept for backward compatibility but is not actively used for garbage collection.

Feature-specific states should be defined in each feature's `feature_setting.py`, not in this global file.
