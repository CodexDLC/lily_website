# 🛠️ Codex Tools

A standalone, framework-agnostic Python library for common business logic designed originally for the Lily ecosystem. It is built using the Ports and Adapters (Hexagonal) architecture, making it ready to be separated into a distinct PyPI package.

## 📚 Documentation

The documentation is available in two languages. For technical details, refer to the English version. For architectural concepts and the "why", refer to the Russian version.

- 🇬🇧 **[English Documentation (Technical Specs)](./en_EN/README.md)**
- 🇷🇺 **[Русская документация (Архитектура)](./ru_RU/README.md)**

## 📦 Core Modules

- **`booking`**: Engine for slot calculation and master booking logic.
- **`codex_calendar`**: Utilities for calendar generation.
- **`notifications`**: Abstract builders and template selectors.
- **`common`**: General tools (`loguru` wrap, ARQ queues, redis caching, parsing).
