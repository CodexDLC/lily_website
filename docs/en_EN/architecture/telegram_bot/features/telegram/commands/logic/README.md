# 📂 Commands Logic

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../../README.md)

Business logic layer for the Commands feature.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📜 Orchestrator](./orchestrator.md)** | Start logic and user registration |

## 🏗️ Class: StartOrchestrator

Located in: `src/telegram_bot/features/telegram/commands/logic/orchestrator.py`

```text
BaseBotOrchestrator
  └── StartOrchestrator
```

### Constructor

| Parameter | Type | Description |
|:---|:---|:---|
| `auth_provider` | `AuthDataProvider` (Protocol) | Data access layer (API or DB) |
| `ui` | `CommandsUI` | Pure UI renderer |

### Entry Flow

```text
handle_entry(user_id, payload=User)
│
├── 1. Extract User from payload
├── 2. Build UserUpsertDTO (telegram_id, first_name, username, ...)
├── 3. await self.auth.upsert_user(user_dto)  ← Contract call
├── 4. user_name = user.first_name or "User"
└── 5. return await self.render(user_name)
         └── self.ui.render_start_screen(user_name)
```
