# 🧩 Features

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../README.md)

The `features` directory contains the business logic of the application, organized by domain. Each feature is a self-contained Django app.

## 🗺️ Module Map

| Feature | Description |
|:---|:---|
| **[Main](./main/README.md)** | Core website functionality (pages, views). |
| **[System](./system/README.md)** | System-wide configurations and utilities. |

## 🏗️ Architecture

Each feature follows a standard Django app structure:
- `models.py`: Database schemas.
- `views.py`: Request handlers.
- `urls.py`: URL routing for the feature.
- `admin.py`: Admin interface configuration.
- `apps.py`: App configuration.
