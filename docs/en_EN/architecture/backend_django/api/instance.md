# 📄 API Instance

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

Configuration of the main `NinjaAPI` instance for the `lily_website` project.

## 📋 Overview

The API instance is defined in `api/instance.py`. It uses a specific `urls_namespace` to avoid `ConfigError` during Django's double-import cycles (like autoreload).

## 🛠️ Configuration

- **Title:** `lily_website API`
- **Version:** `1.0.0`
- **Namespace:** `api_v1`
- **Docs Path:** `/api/docs` (Django default for Ninja)

## 💡 Key Features

- **Logging:** Logs initialization details during startup.
- **Isolation:** Defined separately from `urls.py` to prevent circular imports when multiple routers depend on the same instance.
