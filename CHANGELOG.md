# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

## [1.8.0] - 2026-03-06
### Added
- **Documentation:** Comprehensive technical documentation for `codex_tools` (EN/RU) covering engine architecture and DTOs.
- **Codex Tools (Core):** Added support for `parallel_group` and `overlap_allowed` in the booking engine (backend-only for now).
- **Codex Tools (Core):** New `WaitlistEntry` DTO to support future "nearest slot" notification features.

### Changed / Refactored
- **Codex Tools (Booking):** Major internal refactoring of `ChainFinder` and `SlotCalculator` to improve maintainability.
- **Localization:** Translated all internal docstrings, comments, and DTO descriptions in `codex_tools` from Russian to English.
- **Admin UI:** Simplified `PromoMessageAdmin` (removed redundant statistics and design fields).
- **Admin UI:** Removed `TranslationAdmin` from promos to streamline the management interface.
- **DTOs:** Standardized field names in `BookingEngineRequest` and `EngineResult` (e.g., `target_date` -> `booking_date`).

### Fixed
- **Tests:** Updated performance and logic tests to align with the new internal engine architecture.

## [1.7.0] - 2026-03-05
### Added
- **Booking Engine V2:** Fully integrated the new `ChainFinder` engine for atomic booking of service chains.
- **Atomic Rescheduling:** Implemented group rescheduling logic that ensures all services in a visit are moved together while respecting master availability and buffers.
- **Unified Notifications:** Introduced a grouped notification system via Redis cache and ARQ worker, sending a single consolidated email for multiple services in one visit.
- **CRM Enhancements:** Added a "Group Bookings" view in the admin cabinet with mass actions (Approve All, Complete All, Cancel All).
- **CRM Enhancements:** Added a "Show All Dates" quick-reset filter in the appointment calendar widget.
- **Codex Tools:** Extracted core business logic into a standalone `codex_tools` module, including framework-independent calendar and data normalization utilities.

### Fixed
- **UI/UX:** Fixed HTMX target issues that caused interface duplication and "nested" layouts in the admin cabinet.
- **UI/UX:** Standardized the reschedule UI with a unified 10-day date scroller for both single and group records.
- **Data Integrity:** Implemented robust phone and name normalization to prevent duplicate client records across all entry points.
- **Stability:** Fixed a critical `DataError` in the notification worker when processing complex group data in Redis Streams.

### Changed / Refactored
- **Architecture:** Migrated `AppointmentGroup` to support the `Completed` status and atomic state transitions.
- **Code Quality:** Resolved over 300 Ruff linting issues and fixed multiple Mypy typing errors for better codebase maintainability.
- **Internal:** Renamed `codex_tools.calendar` to `codex_tools.codex_calendar` to avoid conflicts with the Python standard library.

## [1.6.3] - 2026-03-02
### Added
- **Analytics:** Implemented "Lazy Load" strategy for GTM and GA4 to significantly improve PageSpeed scores (LCP/TBT).
- **Analytics:** Added a 3-second fallback timer to ensure tracking scripts load even without user interaction.
- **Analytics:** Integrated HTMX tracking by pushing `htmx_page_view` events on virtual page transitions.
- **Dev Tools:** Enhanced `tools/dev/check.py` with robust Docker container status validation and automatic log output for failed services.

### Fixed
- **Worker:** Fixed `ModuleNotFoundError` in `notification_worker` by correcting the `transliterate` utility import path.
- **UI/UX:** Fixed broken translation tag for `service_item_epilation` in the footer.
- **Configuration:** Updated Google Tag Manager ID to the latest active container (`GTM-NR6MRX2C`) in site settings fixtures.

### Changed / Refactored
- **Booking Wizard:** Continued refactoring of the Wizard v2 flow, including updated selectors and step templates (Masters, Calendar, Confirm).
