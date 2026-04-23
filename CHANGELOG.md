# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

For the history of changes before version 2.0.0, see [CHANGELOG_archive.md](docs/CHANGELOG_archive.md).

## [2.4.1] - 2026-04-23

### Fixed

- **Infrastructure:** Restored the missing `system_worker` in production and test Docker configurations.
- **CI/CD:** Updated the deployment workflow to automatically start the `system_worker` on the VPS.

## [2.4.0] - 2026-04-23

### Added

- **Booking Management:** Implemented advanced appointment management with real-time slot overlap validation in the cabinet.
- **Booking Engine:** Introduced `LilyBookingPersistenceHook` for a clean separation of booking creation and notification logic.
- **Cabinet UI:** Enhanced the appointment schedule with HTMX-powered modals and dynamic status updates.
- **Infrastructure:** Integrated Redis-based action tokens for secure, short-lived operations (e.g., booking confirmations).
- **Automation:** Added recovery documentation and streamlined redis backend configuration for workers.

### Fixed

- **Booking Logic:** Resolved issues with availability checks by including `reschedule_proposed` status in the blocking logic.
- **Cabinet:** Added robust error handling and user feedback for slot conflicts during rescheduling.
- **Worker:** Resolved mypy type errors and satisfied logging protocol.
- **Bot:** Restored localization tests and achieved 90% coverage after aiogram-i18n 1.5 migration.

### Changed / Refactored

- **Architecture:** Refactored `BookingRuntimeEngineGateway` and `RuntimeBookingProvider` to support extended appointment filters and validation.
- **Static Assets:** Cleaned up cabinet CSS/JS and optimized the CSS compiler configuration for better performance.
- **UI Aesthetics:** Modernized site aesthetics and simplified site settings serialization.
- **Dev Experience:** Standardized environment templates and updated scratch scripts for catalog management.
- **Bot Dependencies:** Migrated the project to `codex-bot>=0.3.0` with `aiogram>=3.27.0` and `aiogram-i18n[runtime]>=1.5`, removing the direct `fluent.runtime` workaround from the bot dependency group.

## [2.3.0] - 2026-04-22


### Added

- **Maintenance Panel:** Implemented a centralized "System Maintenance" dashboard in the admin cabinet for manual data synchronization and catalog management.
- **Service Search:** Integrated full-text search for the service catalog with mobile UI optimizations.
- **Infrastructure:** Added `FIELD_ENCRYPTION_KEY` support for GitHub Actions CI to ensure encrypted fields don't break automated tests.

### Fixed

- **Dev Tools:** Restored terminal screen clearing in the `check.py` runner for a better developer experience.
- **Linting:** Resolved multiple Ruff errors in `scratch/build_service_fixtures.py` (unused variables and loop controls).
- **Security:** Hardened field encryption by enforcing proper Fernet key validation across all environments.
- **Git:** Optimized repository size by excluding the `archive/` directory from Git tracking and moving it to `.gitignore`.

### Changed / Refactored

- **Architecture:** Refined modularity in the system module to support granular data loading from the admin interface.

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
