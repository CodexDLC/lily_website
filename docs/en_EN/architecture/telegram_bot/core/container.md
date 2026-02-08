# 📜 DI Container

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

The `BotContainer` is the central Dependency Injection hub. It assembles all services, API clients, and feature orchestrators at startup.

**File:** `src/telegram_bot/core/container.py`

---

## 🏗️ Responsibilities

1. **Create API clients** (gateways to backend services)
2. **Run feature discovery** (menu buttons, garbage states)
3. **Build feature orchestrators** via factories from `feature_setting.py`
4. **Store orchestrators** in `self.features` dictionary for Director access

---

## 📋 Constructor Flow

```text
BotContainer.__init__(settings, redis_client)
│
├── 1. Create AuthClient (HTTP gateway to backend)
├── 2. Create FeatureDiscoveryService
├── 3. discovery_service.discover_all()
│       ├── Scan INSTALLED_FEATURES for MENU_CONFIG
│       └── Scan INSTALLED_FEATURES for GARBAGE_COLLECT / STATES
├── 4. self.features = discovery_service.create_feature_orchestrators(self)
│       └── For each feature with create_orchestrator() → call factory
└── 5. Create BotMenuOrchestrator (special case: depends on discovery)
        └── Register as self.features["bot_menu"]
```

---

## 🔑 Key Attributes

| Attribute | Type | Description |
|:---|:---|:---|
| `settings` | `BotSettings` | Environment configuration |
| `redis_client` | `Redis` | Shared Redis connection |
| `auth_client` | `AuthClient` | HTTP client for auth backend |
| `discovery_service` | `FeatureDiscoveryService` | Feature auto-discovery |
| `features` | `dict[str, Any]` | Orchestrator registry (`{key: orchestrator}`) |
| `bot_menu` | `BotMenuOrchestrator` | Dashboard orchestrator (also in `features`) |

---

## 🔌 How Features Access Container

Middleware injects `container` into every handler via aiogram's data propagation:

```python
# In handler:
async def cmd_start(m: Message, container: BotContainer):
    orchestrator = container.features["commands"]
    view_dto = await orchestrator.handle_entry(user_id, payload)
```

---

## 🔄 Two Data Modes (API vs Direct)

The container decides which implementation to inject based on configuration:

```text
API Mode (default):
  container.auth_client → AuthClient (HTTP → FastAPI → DB)

Direct Mode (future):
  container.auth_repository → AuthRepository (→ DB directly)
```

The orchestrator receives a Protocol-typed provider and does not know which mode is active.

---

## 🧹 Shutdown

```python
async def shutdown(self):
    await self.redis_client.close()
```

Called when the bot stops polling to release Redis connections.
