# 📂 Feature Templates

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

Scaffolding templates used by `manage.py` to generate new features.

**Location:** `src/telegram_bot/resources/templates/feature/`

---

## 📋 Available Templates

| Template | Generates | Description |
|:---|:---|:---|
| `feature.py.tpl` | `feature_setting.py` | States, GC config, menu, factory |
| `handlers.py.tpl` | `handlers/handlers.py` | Router with callback handler |
| `orchestrator.py.tpl` | `logic/orchestrator.py` | Orchestrator with `handle_entry` |
| `state_manager.py.tpl` | `logic/state_manager.py` | Draft storage manager |
| `ui.py.tpl` | `ui/ui.py` | UI renderer |
| `contract.py.tpl` | `contracts/contract.py` | Protocol interface |
| `callbacks.py.tpl` | `resources/callbacks.py` | CallbackData classes |
| `texts.py.tpl` | `resources/texts.py` | Text constants |
| `keyboards.py.tpl` | `resources/keyboards.py` | Keyboard builders |
| `formatters.py.tpl` | `resources/formatters.py` | Data formatters |

---

## 🔧 Template Variables

Templates use Python `str.format()` placeholders:

| Variable | Example | Description |
|:---|:---|:---|
| `{feature_key}` | `my_feature` | Snake_case feature name |
| `{class_name}` | `MyFeature` | PascalCase class prefix |

---

## 🚀 Usage

```bash
python -m src.telegram_bot.manage create_feature my_feature
```

This generates the complete feature structure with all files from templates. After generation, add the feature to `INSTALLED_FEATURES` in `settings.py`.
