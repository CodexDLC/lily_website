# 📄 Bot Menu Orchestrator

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../README.md)

The `BotMenuOrchestrator` is a universal dashboard manager that handles navigation and access control for the bot's main interface.

## 🛠️ Core Responsibilities

Located in: `src/telegram_bot/features/telegram/bot_menu/logic/orchestrator.py`

### 1. `render_dashboard(user_id: int, chat_id: int, mode: str = "bot_menu") -> UnifiedViewDTO`

The primary method for generating the dashboard view.

*   **Modes**: Supports two primary modes: `bot_menu` (User/General) and `dashboard_admin` (Admin-only).
*   **Access Control**:
    *   If `mode="dashboard_admin"` is requested, it verifies if the user is an admin or owner.
    *   If the check fails, it silently falls back to the standard `bot_menu`.
*   **Dynamic Discovery**: Fetches available features from the `MenuDiscoveryProvider` based on the current mode and user permissions.

### 2. `handle_menu_click(target: str, user_id: int, chat_id: int) -> UnifiedViewDTO | None`

Processes button clicks from the dashboard.

*   **Internal Navigation**: If the `target` is a dashboard mode (`dashboard_admin` or `bot_menu`), it simply re-renders the dashboard in that mode.
*   **External Navigation**: If the `target` is a specific feature (e.g., `commands`, `notifications`):
    1.  Verifies access permissions for that specific feature.
    2.  Uses the `Director` to transition the bot's state to the target feature.

### 3. `handle_callback(ctx: MenuContext) -> UnifiedViewDTO | None`

The entry point for Telegram callback queries. It parses the `MenuContext` and routes the request to either `handle_entry` (for opening menus) or `handle_menu_click` (for processing selections).

## 🔐 Access Control Logic

The orchestrator uses two helper methods for security:

*   **`_is_user_admin`**: Checks if the user ID is in the `owner_ids_list` or `superuser_ids_list`.
*   **`_check_access`**: Evaluates a feature's configuration (`is_superuser`, `is_admin`) against the user's actual permissions.

## 📝 Key Features

*   **Role-Based UI**: Admins see a different set of buttons than regular users.
*   **Seamless Transitions**: Switching between User and Admin dashboards happens within the same message (edit mode).
*   **Decoupled Navigation**: The orchestrator doesn't know the details of other features; it relies on the `Director` and `DiscoveryProvider` to handle transitions.
