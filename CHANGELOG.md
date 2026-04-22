# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

## [1.9.2] - 2026-03-15

### Added
- **API Documentation:** Expanded technical documentation with detailed specifications for `admin`, `booking`, `instance`, `promos`, and `urls` endpoints.
- **Documentation:** Added new feature-specific guides for `cabinet` and `promos` modules.
- **Testing:** Introduced permission-based test suite for the admin cabinet and centralized `conftest.py` for API testing.

### Changed / Refactored
- **Cabinet:** Refined logic and UI for appointment, contact request, and master management views.
- **Notifications:** Updated notification worker services and refined localized booking email templates.
- **Dependencies:** Synchronized project dependencies in `pyproject.toml` and `poetry.lock`.

### Fixed
- **Cleanup:** Removed obsolete Telegram bot files and temporary initialization scripts.
- **CI/CD:** Fixed minor issues in the automated project initialization and check tools.

## [1.9.1] - 2026-03-11

## [2.2.0] - 2026-04-19

### Added

- **Bot:** Major overhaul of the Telegram bot's redis-backed notification handling and UI orchestration.
- **Bot:** Introduced centralized container-based dependency injection for better testing and modularity.

### Changed / Refactored

- **Bot:** Refactored command logic and stream processors to simplify bot interactions.

## [2.1.0] - 2026-04-19

### Added

- **Workers:** Introduced `system_worker` for handling background tasks like booking operations, email imports, and tracking flushes.
- **Workers:** Expanded `notification_worker` capabilities and standardized task aggregators.

### Changed / Refactored

- **Workers:** Centralized worker configuration and core logic (heartbeats, internal API, streams).

## [2.0.0] - 2026-04-19

### Added

- **Tracking:** Implemented a new internal analytics and page view tracking system with Redis-backed buffering and asynchronous flushing.
- **System:** Major reorganization of the system module. Introduced new models for `Client`, `SiteSettings`, `EmailContent`, `SEO`, and `StaticTranslation`.
- **Management:** New suite of migration commands for legacy data (categories, services, masters, clients, appointments).
- **Templates:** Introduced a comprehensive set of new templates for emails, error pages, and features (booking, conversations, main) using a modular structure.

### Changed / Refactored

- **Architecture:** Fully migrated the project from the legacy `backend_django` structure to the new `lily_backend` architecture.
- **Templates:** Reorganized and standardized all HTML templates to align with the new feature-based layout.
- **Core:** Consolidated shared logic and constants into `src/shared/`.

### Fixed

- **Dev Experience:** Updated `tools/dev/check.py` and other development utilities to support the new project structure.
- **Stability:** Resolved runtime warnings and improved logging performance across the core and shared modules.
