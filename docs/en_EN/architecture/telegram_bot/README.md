# 📂 Telegram Bot Architecture

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../README.md)

Documentation and development plans for the Telegram Bot application located in `src/telegram_bot`.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📂 Core Infrastructure](./core/README.md)** | DI Container, Configuration, and Settings |
| **[📂 Features (Modules)](./features/README.md)** | Modular business logic (Menu, Commands) |
| **[📂 Services](./services/README.md)** | Shared services (Director, FSM, Sender, Animation) |
| **[📂 Infrastructure](./infrastructure/README.md)** | API Routes, Migrations, Models, Redis, Repositories |
| **[📂 Middlewares](./middlewares/README.md)** | Throttling, Security, User Validation, I18n |
| **[📂 Resources](./resources/README.md)** | Templates, Texts, and Keyboards |
| **[📂 Tasks](./tasks/README.md)** | Architectural plans and task lists |

## 🏗️ Project Structure

Below is the structure of the `src/telegram_bot` directory.

### Application Code

```text
src/telegram_bot/
 ┣ 📂 core                  # Core Architecture (DI, Config, Settings)
 ┣ 📂 features              # Modular Features (Plugins)
 ┃ ┣ 📂 redis               # Redis-based features (Notifications, Errors)
 ┃ ┗ 📂 telegram            # Telegram-based features (Menu, Commands)
 ┣ 📂 infrastructure        # Data Access & System Layer
 ┣ 📂 middlewares           # Update processing pipeline
 ┣ 📂 resources             # Static assets (Templates, Locales)
 ┣ 📂 services              # Shared Business Services
 ┗ 📜 app_telegram.py       # Entry Point (Polling)
```

## 📦 Key Concepts

Quick access to architectural concepts.

*   **🧩 Feature-Based Architecture**
    *   Each feature is an isolated module with its own `feature_setting.py` manifest.
    *   Features are pluggable via `INSTALLED_FEATURES`.

*   **🎬 Director & Orchestrator**
    *   **Director:** Manages global navigation (switching between features).
    *   **Orchestrator:** Manages logic within a feature (Data -> UI).

*   **📱 Bot Menu (Dashboard)**
    *   A persistent "Dashboard" message.
    *   Buttons are auto-discovered from features via `MENU_CONFIG`.
