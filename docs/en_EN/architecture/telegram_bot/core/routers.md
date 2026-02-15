# 📜 Routers

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This module is responsible for centralizing and managing the registration of Aiogram routers within the Telegram bot application. It provides functions to automatically discover and include routers from installed features, forming the main application router.

## `collect_feature_routers` Function

```python
def collect_feature_routers() -> list[Router]:
```
Scans the `INSTALLED_FEATURES` (defined in `settings.py`) for Aiogram routers. Each feature is expected to have a `handlers.py` module containing a `router` instance.

**Process:**
1.  Iterates through each `feature_path` specified in `INSTALLED_FEATURES`.
2.  Constructs the module path for the `handlers.py` file within each feature (e.g., `src.telegram_bot.features.bot_menu.handlers`).
3.  Dynamically imports the `handlers` module.
4.  Attempts to retrieve a variable named `router` from the imported module.
5.  If `router` exists and is an instance of `aiogram.Router`, it is added to the list of collected routers.
6.  Logs the status of router loading for each feature (loaded, no handlers, or error).

**Returns:**
A list of `aiogram.Router` instances collected from the installed features.

## `build_main_router` Function

```python
def build_main_router() -> Router:
```
Assembles the main application router by including all collected feature routers and common FSM handlers. This function is the entry point for routing updates to the appropriate handlers.

**Process:**
1.  Initializes a main `Router` instance with the name "main\_router".
2.  Calls `collect_feature_routers()` to get all routers from installed features.
3.  Includes all feature routers and the `common_fsm_router` (from `src.telegram_bot.services.fsm.common_fsm_handlers`) into the `main_router`.
4.  Logs the number of UI features loaded.

**Returns:**
The fully assembled `aiogram.Router` instance, ready to handle incoming updates.
