# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

For the history of changes before version 2.0.0, see [CHANGELOG_archive.md](docs/CHANGELOG_archive.md).

## [2.7.0] - 2026-04-26

### Added

- **Campaigns:** Introduced delivery status tracking API for marketing campaigns, allowing real-time updates from workers.

### Changed

- **Workers:** Enhanced email import logic with robust HTML-to-text extraction that preserves line structure and improves readability.
- **Security:** Hardened the system entrypoint to prevent accidental legacy migrations in production by enforcing `DEBUG` mode requirement.
- **Fixtures:** Updated pricing for cosmetology services and refreshed master availability data in system fixtures.
- **Architecture:** Refactored Ninja API routing to `core/urls.py` to prevent circular imports during system startup.

### Fixed

- **Conversations:** Implemented Phase 1 of the Messaging Migration, resolving the "compose-new" email dispatch bug in the cabinet.
- **Booking:** Fixed incorrect timezone display in notification contexts and client history by ensuring all timestamps are localized.
- **Cabinet:** Added visual indicators for group bookings in the appointment schedule table.
- **Infrastructure:** Silenced linter warnings in Docker configuration and fixed session handling in maintenance views.
- **Tests:** Updated integration and unit tests for booking and conversations to align with recent architectural changes.

## [2.6.0] - 2026-04-25

### Added

- **Notifications:** Added 21 missing email content keys for various booking statuses to eliminate system warnings.

### Changed

- **Infrastructure:** `SITE_BASE_URL` is now automatically synchronized from environment variables to the database during initialization, ensuring correct links across all environments.
- **Infrastructure:** Updated GitHub Actions to use Node.js 24 compatible versions (docker/build-push-action@v6) to resolve deprecation warnings.
- **Fixtures:** Updated default Saturday working hours to `09:00 - 18:00` and set "Lily" as the default contact person.

### Fixed

- **Booking:** Resolved a critical bug where missing `.html` extension in admin notification paths caused public booking failures.
- **Notifications:** Fixed `NotificationRecipient` model to allow adding recipients via the cabinet UI (resolved `NOT NULL` constraint on the note field).
- **Security:** Corrected Magic Login links in emails to prioritize the production domain from `.env` over stale local database values.
- **Cabinet UX:** Removed `required` validation from the "Add Recipient" field that previously blocked saving general site settings.

## [2.5.0] - 2026-04-25

### Added

- **Campaigns:** Implemented full email marketing campaign cycle including composing, previewing, and tracking in the cabinet.
- **Workers:** Added dedicated worker tasks for asynchronous campaign email distribution and event tracking.
- **Infrastructure:** Introduced `CONVERSATIONS_VISION.md` documenting the long-term messaging and CRM roadmap.

### Changed / Refactored

- **Notifications:** Successfully migrated administrative and booking alerts from Telegram to a centralized, reliable email-based notification system.
- **Cabinet:** Reorganized the cabinet URL architecture into a modular package structure for better scalability.
- **Booking Wizard:** Enhanced the public booking experience with a modernized UI, improved stepper logic, and real-time summary panels.

### Fixed

- **Tests:** Restored 90% system-wide test coverage by updating integration and unit tests for the new notification and campaign workflows.

## [2.4.5] - 2026-04-24

### Fixed

- **Localization:** Fixed Redis-backed `static_content` caching so translations are now isolated per language instead of leaking the first warmed locale across the entire site.
- **SEO:** Fixed `canonical` and `hreflang` tags to emit absolute production URLs derived from the configured site base URL.
- **Robots / AI Context:** Corrected `robots.txt` sitemap output and restored localized `llms.txt` support for German, English, Russian, and Ukrainian, including language-aware routing with fallback.
- **Production Cookies:** Hardened production CSRF cookie handling for the canonical non-`www` domain and introduced a fresh cookie name to bypass stale duplicate browser cookies after deploy.

## [2.4.2] - 2026-04-23

### Fixed

- **Infrastructure:** Resolved Redis authentication issues in the backend by switching from DSN-based connection to direct parameter passing, preventing issues with special characters in passwords.

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
