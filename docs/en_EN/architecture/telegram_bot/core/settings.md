# 📜 Settings (Feature Registration)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Django-inspired configuration that declares which features and middleware are active.

**File:** `src/telegram_bot/core/settings.py`

---

## 🧩 INSTALLED_FEATURES

```python
INSTALLED_FEATURES: list[str] = [
    "features.commands",
    "features.bot_menu",
    "features.errors",
]
```

Each string is a **dotted path** relative to `src/telegram_bot/`.

### What Happens at Startup

The bot reads this list and automatically:

1. **Imports routers** from `{feature}.handlers` (via `routers.py`)
2. **Discovers menu buttons** from `{feature}.menu` → `MENU_CONFIG` (via `FeatureDiscoveryService`)
3. **Registers garbage states** from `{feature}.feature_setting` → `GARBAGE_COLLECT` (via `FeatureDiscoveryService`)
4. **Creates orchestrators** from `{feature}.feature_setting` → `create_orchestrator()` (via `FeatureDiscoveryService`)

### Adding a New Feature

1. Create the feature package under `features/`
2. Add `handlers/__init__.py` that exports `router`
3. Add `feature_setting.py` with `STATES`, `GARBAGE_COLLECT`, `create_orchestrator()`
4. Add the path to `INSTALLED_FEATURES`

Or use the CLI generator:

```bash
python -m src.telegram_bot.manage create_feature my_feature
```

---

## 🛡️ MIDDLEWARE_CLASSES

```python
MIDDLEWARE_CLASSES: list[str] = [
    "middlewares.user_validation.UserValidationMiddleware",
    "middlewares.throttling.ThrottlingMiddleware",
    "middlewares.security.SecurityMiddleware",
    "middlewares.container.ContainerMiddleware",
]
```

**Order matters:** first in the list wraps all subsequent middleware.

| Middleware | Purpose |
|:---|:---|
| `UserValidationMiddleware` | Ensures `from_user` exists on every update |
| `ThrottlingMiddleware` | Redis-based rate limiting |
| `SecurityMiddleware` | Session hijacking protection |
| `ContainerMiddleware` | Injects `BotContainer` into handler kwargs |
