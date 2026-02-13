# ⚙️ Core Module

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../README.md)

The `core` module contains the fundamental configuration and entry points for the Django application. It handles settings, URL routing, and WSGI/ASGI interfaces.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **Settings** | Configuration split into `base`, `dev`, and `prod` environments. |
| **URLs** | Root URL configuration (`urls.py`). |
| **WSGI/ASGI** | Entry points for web servers. |

## 🛠️ Settings Architecture

The project uses a split-settings approach located in `core/settings/`.

### `base.py`
Contains common settings shared across all environments:
- **Apps:** `modeltranslation`, `django.contrib.*`, `features.*`, `ninja`.
- **Middleware:** Security, Session, CSRF, Auth, Messages, Clickjacking, Locale.
- **Templates:** Configured with context processors for auth, messages, i18n, and site settings.
- **I18n:** German (default), Russian, Ukrainian, English.
- **Static/Media:** Standard configuration.

### `dev.py`
Settings for local development (debug mode, local database).

### `prod.py`
Settings for production (PostgreSQL, security hardening).

## 🔐 Environment Variables

The project uses `python-dotenv` to load secrets from a `.env` file.

Key variables:
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `LANGUAGE_CODE`
- `TIME_ZONE`

## 🌐 URL Configuration

The root `urls.py` delegates routing to:
- Django Admin
- API (Django Ninja)
- Feature-specific URLs
- Internationalization patterns (`i18n_patterns`)
