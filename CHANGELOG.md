# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

For the history of changes before version 2.0.0, see [CHANGELOG_archive.md](docs/CHANGELOG_archive.md).

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
