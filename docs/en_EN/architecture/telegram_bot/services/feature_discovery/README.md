# 📂 Feature Discovery Service

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

Automatically scans `INSTALLED_FEATURES` and extracts configuration from each feature.

**File:** `src/telegram_bot/services/feature_discovery/service.py`

---

## 🎯 Purpose

Instead of manually wiring every feature's menu buttons, garbage states, and orchestrator factories, this service uses `importlib` to scan feature packages and extract configuration dynamically.

---

## 🏗️ Class: FeatureDiscoveryService

### Discovery Methods

| Method | What It Finds | Source |
|:---|:---|:---|
| `discover_all()` | Menu buttons + garbage states | Called at startup |
| `get_menu_buttons()` | `MENU_CONFIG` dicts | `{feature}.menu` module |
| `create_feature_orchestrators(container)` | Orchestrator instances | `{feature}.feature_setting.create_orchestrator()` |

---

## 🔄 Discovery Flow

```text
discover_all()
│
└── For each feature in INSTALLED_FEATURES:
    ├── _discover_menu(feature_path)
    │   └── Import {feature}.menu → get MENU_CONFIG
    └── _discover_garbage_states(feature_path)
        └── Import {feature}.feature_setting
            ├── If GARBAGE_STATES → register explicit list
            └── If GARBAGE_COLLECT=True → register STATES
```

```text
create_feature_orchestrators(container)
│
└── For each feature in INSTALLED_FEATURES:
    └── Import {feature}.feature_setting
        └── If create_orchestrator exists → call factory(container)
            └── Store result in {key: orchestrator} dict
```

---

## 📋 Feature Detection Strategy

The service looks for `feature_setting.py` first, then falls back to `__init__.py`:

```text
Candidates:
  1. src.telegram_bot.{feature}.feature_setting
  2. src.telegram_bot.{feature}
```

---

## 🔗 Integration

Called by `BotContainer` during initialization:

```python
self.discovery_service = FeatureDiscoveryService()
self.discovery_service.discover_all()
self.features = self.discovery_service.create_feature_orchestrators(self)
```
