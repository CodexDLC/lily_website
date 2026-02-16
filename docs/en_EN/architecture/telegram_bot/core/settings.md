# 📜 Settings

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This module centralizes the configuration for pluggable features and middleware within the Telegram bot application. It defines lists of installed features (both interface-based and Redis Stream listeners) and middleware classes, enabling modularity and easy management of the bot's functionalities.

## `INSTALLED_FEATURES`

```python
INSTALLED_FEATURES: list[str] = [
    "features.telegram.commands",
    "features.telegram.bot_menu",
    "features.telegram.notifications",
]
```
A list of strings, where each string represents the path to an interface-based feature (i.e., features that expose Aiogram routers). These features are automatically discovered and included in the main application router by the `routers` module.

## `INSTALLED_REDIS_FEATURES`

```python
INSTALLED_REDIS_FEATURES: list[str] = [
    "features.redis.notifications",
    "features.redis.errors",
]
```
A list of strings, where each string represents the path to a feature that acts as a listener for Redis Streams. These features typically process background tasks or events received via Redis.

## `MIDDLEWARE_CLASSES`

```python
MIDDLEWARE_CLASSES: list[str] = [
    "middlewares.user_validation.UserValidationMiddleware",
    "middlewares.throttling.ThrottlingMiddleware",
    "middlewares.security.SecurityMiddleware",
    "middlewares.container.ContainerMiddleware",
]
```
A list of strings, where each string is the full import path to a middleware class. These middleware classes are applied to incoming updates, allowing for cross-cutting concerns such as user validation, throttling, security, and dependency injection.
