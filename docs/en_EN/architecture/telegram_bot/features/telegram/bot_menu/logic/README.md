# 📂 Bot Menu Logic

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

Business logic layer for the Bot Menu feature.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📜 Orchestrator](./orchestrator.md)** | Main coordinator: menu assembly, RBAC, navigation |

## 🏗️ Class: BotMenuOrchestrator

Located in: `src/telegram_bot/features/telegram/bot_menu/logic/orchestrator.py`

### Responsibilities

1. **Menu Assembly**: Fetches all available feature configurations via the `MenuDiscoveryProvider`.
2. **Access Control**: Validates user permissions (Admin/Superuser) for specific menu buttons.
3. **Navigation Handling**: Processes menu clicks and prepares state transitions to target features.

### Key Methods

#### `render_menu(user_id: int)`

- Retrieves all registered menu buttons from the discovery service.
- Filters buttons based on the user's role.
- Calls the UI layer to render the final `UnifiedViewDTO`.

#### `handle_menu_click(target: str, user_id: int)`

- Validates access to the target feature.
- Returns a `UnifiedViewDTO` with a `next_state` header for FSM state transition.

## 🔄 State Management

The `bot_menu` operates in the `BotMenuStates.main` state. When a user navigates to another feature, the orchestrator provides the new state name, and the `Director` updates the FSM context.
