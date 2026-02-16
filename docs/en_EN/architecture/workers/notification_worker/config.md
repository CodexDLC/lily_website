# 📜 Config

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This module defines the `WorkerSettings` class, which encapsulates configuration parameters specific to the Notification Worker. It uses Pydantic's `BaseSettings` to load settings from environment variables (e.g., from a `.env` file).

## `WorkerSettings` Class

The `WorkerSettings` class holds various configuration values necessary for the Notification Worker's operation, including Redis connection details, global site settings, and paths to templates.

### Fields

*   `REDIS_HOST` (`str`): The hostname or IP address of the Redis server (default: `"localhost"`).
*   `REDIS_PORT` (`int`): The port number of the Redis server (default: `6379`).
*   `SITE_URL` (`str`): The base URL of the main website (default: `"http://localhost:8000"`).
*   `LOGO_URL` (`str`): The URL to the site's logo, used in templates (default: a specific Pinlite URL).
*   `BASE_DIR` (`Path`): The absolute path to the project's root directory (`lily_website`).
*   `TEMPLATES_DIR` (`Path`): The absolute path to the worker's templates directory.

### `Config` Inner Class

The `Config` inner class provides Pydantic-specific configurations:

*   `env_file`: Specifies that settings should be loaded from a `.env` file.
*   `extra = "ignore"`: Instructs Pydantic to ignore any extra fields found in the environment variables that are not defined in `WorkerSettings`.

## `settings` Instance

```python
settings = WorkerSettings()
```
A global instance of `WorkerSettings` is created, making the configured settings readily available throughout the Notification Worker application.
