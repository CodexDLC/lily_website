# 📂 Bot Menu (Dashboard)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

The `bot_menu` feature is the central hub (Dashboard) of the Telegram Bot. It provides a persistent interface with buttons that allow users to navigate between different installed features and switch between User and Admin modes.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📂 Handlers](./handlers/README.md)** | Entry points and callback processing |
| **[📂 Logic](./logic/README.md)** | Business logic and orchestrator |
| **[📂 Contracts](./contracts/README.md)** | Data access interfaces (MenuDiscoveryProvider) |
| **[📂 UI](./ui/README.md)** | Message rendering and keyboards |
| **[📂 Resources](./resources/README.md)** | Static texts and constants |

## 📋 feature_setting.py

```python
class BotMenuStates(StatesGroup):
    main = State()

STATES = BotMenuStates
GARBAGE_COLLECT = True
```

## 🔄 Logic Flow

1. **Entry**: User triggers the menu (e.g., via `/start`).
2. **Mode Selection**: Orchestrator determines if the user should see the Admin or User dashboard.
3. **Discovery & Filtering**: Orchestrator fetches registered buttons and filters them by user permissions.
4. **Rendering**: `BotMenuUI` creates a keyboard with the allowed buttons.
5. **Navigation**: When a button is clicked, the orchestrator either switches the dashboard mode or uses the `Director` to move to another feature.

## 🧩 Menu Integration

Other features appear in this menu by defining a `MENU_CONFIG` in their own `feature_setting.py`. The `bot_menu` itself does not need to be modified to add new buttons.
