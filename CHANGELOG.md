# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

## [1.9.3] - 2026-03-17

### Added
- **System (Fixtures):** Implemented fixture versioning using SHA-256 hashing to track changes and optimize loading performance by preventing redundant data updates.
- **System (Notifications):** Major refactoring and decoupling of the notification system from the Telegram bot; migrated templates and added a dedicated email preview tool (`tools/dev/preview_emails.py`).

### Fixed
- **System (Promos):** Applied review fixes and improved system reliability. Updated `PromoMessage` statuses to `TextChoices` and synchronized admin UI badge colors with status slugs.
- **UI/UX:** Fixed layout issues in localized booking email templates and updated cabinet UI styles.
- **Management:** Hardened management commands (`update_all_content`, `load_services`) with improved error collection and logging.

### Changed / Refactored
- **Cleanup:** Removed obsolete Telegram bot handlers, legacy contracts, and redundant test/helper files.
- **Git:** Updated `.gitignore` to strictly exclude the `.claude/` directory and local settings.

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

### Fixed
- **CRM:** Fixed `AttributeError` in `ContactRequestsView` by replacing the non-existent `send_universal` method with the correct `send_admin_reply` service call. This restores the ability to reply to contact requests via email from the admin cabinet.

## [1.9.0] - 2026-03-11

### Added
- **Booking Engine V2:** Finalized integration of the atomic booking engine with Django adapters and DTOs.
- **Models:** Added `timezone` field to `Master` and `lang` (language) to `Appointment` and `AppointmentGroup` for better internationalization support.
- **Migrations:** Implemented migrations `0010` and `0011` to support new booking features.
- **Notifications:** Added a new email template `bk_receipt.html` for booking confirmations.

### Fixed
- **Security:** Patched critical vulnerabilities by updating `django` to `5.2.12` (CVE-2026-25674) and `pillow` to `12.1.1` (CVE-2026-25990).
- **Security:** Resolved multiple `Bandit` security issues (missing timeouts in tests, unsafe HTML rendering in admin).
- **Telegram Bot:** Fixed an issue where `localhost` URLs in delete inline buttons caused message delivery failure.

### Changed / Refactored
- **Telegram Bot:** Major refactoring of the notification system (`BookingProcessor`, `NotificationsUI`, `Keyboards`).
- **SEO:** Migrated Service-specific SEO data directly into service fixtures; deprecated and removed `initial_seo.json`.
- **Infrastructure:** Updated Nginx configurations and optimized GitHub Actions workflows for deployment.
- **Dev Experience:** Disabled automatic `SiteSettings` overwrite from fixtures to preserve local development configurations (e.g., `localhost`).
- **Project Cleanup:** Removed obsolete `BOOKING_ENGINE_V2_PLAN.md` and temporary structure files.
- **Git:** Updated `.gitignore` to strictly exclude local logs, `nul` files, and temporary project structure reports.

## [1.8.1] - 2026-03-07
### Fixed
- **UI/UX:** Fixed "nested" layout duplication in the admin cabinet by restoring `HtmxCabinetMixin` logic for HTMX requests.
- **Admin UI:** Fixed `SystemCheckError` in `ClientAdmin` and `PromoMessageAdmin` by aligning admin fields with actual model attributes.
- **Admin UI:** Refactored `status_badge` in all admin modules to use non-translated keys for color mapping, improving robustness in multi-language environments.
- **PWA:** Replaced hardcoded hex colors in the PWA install banner with CSS variables (`--color-emerald`, `--color-gold`) for better maintainability.
- **Tools:** Improved error handling and simplified logic in the `resize_image.py` utility.

### Added
- **Media:** Added optimized mobile assets and small logo for better performance.

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

## [1.5.0] - 2026-02-27
### Added
- **Cabinet:** Implemented full appointment reschedule logic with interactive calendar and HTMX-powered slot selection.
- **Logging:** Introduced a unified logging standard across Backend, Shared, and Workers for better observability.
- **Documentation:** Added a comprehensive Global Roadmap and detailed technical task specifications (TASK-GLOBAL-*, TASK-206-210).
- **Infrastructure:** Added `logging_standard.md` and updated development principles for the team.

### Changed / Refactored
- **Booking:** Major refactoring of booking services (`reschedule.py`, `session.py`, `slots.py`) to support flexible appointment adjustments.
- **Cabinet:** Improved architecture by separating selectors and services for appointment management.
- **System:** Enhanced Redis managers for site settings and notification caching for better performance.
- **Workers:** Updated notification processors and email templates for more robust delivery.

### Fixed
- **API:** Resolved issues in booking and promo validation logic.
- **Management:** Improved stability of data migration and content update commands.

## [1.4.2] - 2026-02-26
### Added
- **Quality Control:** Integrated `test_templates_syntax.py` to automatically verify Django template syntax during tests.
- **Security:** Added `Bandit` for static security analysis and `detect-secrets` to prevent accidental credential leaks.
- **Documentation:** Added `markdownlint` to ensure high-quality and consistent Markdown documentation.
- **Automation:** Updated `tools/dev/check.py` to include all new quality and security checks in the local development workflow.

### Fixed
- **Templates:** Resolved `TemplateSyntaxError` in `cabinet/appointments/list.html` (duplicate `{% empty %}` tag).
- **Templates:** Fixed incorrect `{% get_current_language %}` usage in `cabinet/auth/magic_link.html`.
- **Security:** Replaced `random.randint` with `secrets.randbelow` for cryptographically strong bot access codes in `Master` model.
- **Security:** Enabled `autoescape` in Jinja2 environment for worker templates.

## [1.4.1] - 2026-02-26
### Fixed / Refactored
- **CSS:** Major cleanup of legacy Telegram Mini App (TMA) styles. Removed `tma_app.css`, `tma_base.css`, and related directory.
- **CSS:** Consolidated styles into `cabinet.css` and `cabinet_app.css` for better maintainability.
- **Settings:** Updated core settings to reflect the new static assets structure.

## [1.4.0] - 2026-02-26
### Added
- **Cabinet:** Full refactoring of appointment management using **HTMX**. Confirmations, cancellations, and edits now occur without page reloads.
- **Cabinet:** Extracted appointment card to a reusable partial template `_appointment_card.html`.
- **Cabinet:** Implemented management dashboard, clients, and masters management sections.
- **UI:** Added booking rules page (`booking rules`).

### Changed / Refactored
- **Data Seeding:** Migrated initial data loading from migrations to specialized management commands (`load_main_data`) for deployment stability.
- **Security:** Enhanced `AdminRequiredMixin` with explicit authentication and role-based redirection logic.
- **Architecture:** Renamed `profile.py` to `user_profile.py` to avoid shadowing Python's standard library.
- **Cleanup:** Removed obsolete and redundant JSON fixtures.

### Fixed
- **i18n:** Corrected German notification texts (removed remaining Cyrillic fragments).

## [1.3.0] - 2026-02-24
### Added
- **Admin Tools:** Implemented comprehensive case management and manual booking tool in TMA with client history support and past date entry.
- **Client Service:** Introduced robust E.164 phone normalization logic to prevent duplicate client records.
- **TMA Appointments:** Added management view for confirming, cancelling, and updating existing appointments directly from Telegram.
- **Bot:** Added "propose alternative time" flow on appointment rejection.
- **UI:** Implemented Bento cross-linking on service detail pages and optimized PWA static file serving (`manifest.json`, `sw.js`).

### Fixed
- **Code Quality:** Resolved multiple Ruff linter errors (E701, N806, SIM105, W291) and optimized cache invalidation for static content.
- **Security:** Corrected import paths for `tma_secure_required` decorator.


## [1.2.2] - 2026-02-22
### Fixed
- **Migrations:** Resolved `InconsistentMigrationHistory` in `main` app by restoring the correct dependency chain (`0001` -> `0002` -> `0003` -> `0004`).

## [1.2.1] - 2026-02-22
### Legal & Maintenance
- **Fixed:** Critical localization errors in legal templates (`datenschutz.html`, `impressum.html`). Removed mixed Cyrillic/German text.
- **Docs:** Fixed markdown table formatting in technical documentation for better rendering.
- **Optimization:** Refactored cache invalidation logic in `Service` and `PortfolioImage` models (removed redundant keys).

## [1.2.0] - 2026-02-21
### Telegram Mini App & Admin Features
- **TMA:** Full implementation of Telegram Mini App (TMA) for client interactions (contacts, forms, styles).
- **Bot:** New `contacts_admin` feature for managing contact requests directly from Telegram.
- **i18n:** Major refactoring of static content translation. Moved static strings to database (`StaticTranslation` model).
- **Infrastructure:** New Redis managers for site settings, notifications, and admin dashboard caching.
- **System:** Expanded `SiteSettings` with social media URLs, logo configuration, and bot integration.
- **API:** Added secure API routes for admin dashboard and TMA interactions.
- **Worker:** Enhanced email templates for client replies and receipts.

## [1.1.3] - 2026-02-19
### SEO & Infrastructure Hardening
- **SEO:** Complete overhaul of `sitemap.xml` generation with full multilingual support (`hreflang`, `x-default`).
- **SEO:** Enforced `CANONICAL_DOMAIN` (`https://lily-salon.de`) for all sitemap links, canonical tags, and OpenGraph URLs.
- **Infrastructure:** Configured Nginx to strictly redirect HTTP -> HTTPS and `www` -> non-`www`.
- **Dev Tools:** Enhanced `tools/dev/check.py` with auto-fix capabilities and full project scanning.
- **Fixed:** Resolved `NoReverseMatch` errors in sitemap generation for i18n routes.
- **Fixed:** Corrected type hints in project initialization scripts (`tools/init_project`).
- **Fixed:** Deployment issue by removing explicit command for backend to allow `entrypoint.sh` execution.
- **Fixed:** Service category assignment logic in `load_services` management command.

## [1.1.2] - 2026-02-19
### Notifications Reliability
- **Added:** SendGrid API fallback implementation for reliable email delivery.
- **Added:** Isolated test environment configuration for notification services.
- **Fixed:** Admin category display issues.

## [1.1.1] - 2026-02-19
### Dev Experience
- **Fixed:** Synchronized local development checks (`tools/dev/check.py`) with CI pipeline.
- **Added:** Automated Docker resource cleanup in dev tools.

## [1.1.0] - 2026-02-18
### Workers & Promo Architecture
- **Refactor:** Major reorganization of worker architecture and notification flow.
- **Added:** Autonomous worker flow with race condition protection for notification statuses.
- **UI:** Draggable and collapsible Promo Widget implemented with pure CSS/JS.
- **Fixed:** Notification flow logic to prevent duplicate sends.

---

## [1.0.7] - 2026-02-18
### Booking & Optimization
- **Added:** Master Day Off functionality (blocking specific dates for masters in booking wizard).
- **Improved:** Performance & Architecture optimization (removed legacy assets, instructions, and scripts).
- **Fixed:** Enhanced error handling in `site_settings` context processor (Redis/DB fallbacks).

---

## [1.0.0 - 1.0.6] - 2026-02-17
### Major Release: SEO & Security
- **Security:** Removed client phone numbers from Telegram notifications (privacy hardening).
- **SEO:** Ultimate optimization for "Nagelstudio Köthen", "Gutscheine", and "Online Booking".
- **UI:** Reordered Bento grid to highlight Nails and Eyes as primary services.
- **Fixed:** Restored Team page layout and styles (v0.9.2 parity).
- **Fixed:** Resolved Promo Admin CTR display errors and import conflicts.

---

## [0.9.9 - 0.9.17] - 2026-02-16
### Bot Architecture & i18n
- **Added:** New Telegram Bot architecture with full internationalization (i18n) support.
- **Added:** GDPR-compliant GA4/GTM tracking and cookie consent banner.
- **Fixed:** Critical fixes in booking logic, API authentication, and master selection.
- **Fixed:** Resolved Ruff linting issues and type-checking warnings.

---

## [0.9.3] - 2026-02-16
### Worker Stability & SMTP Fixes
- **Added:** Automatic retry mechanism for ARQ workers (5 retries with 10s delay).
- **Improved:** Added explicit connection timeout (15s) for SMTP client to prevent worker hanging.
- **Improved:** Detailed logging for SMTP connection attempts (host, port, SSL/TLS status).
- **Fixed:** Enhanced error handling for `SMTPConnectError` in email tasks.

---

## [0.9.0] - 2026-02-16
### MVP Candidate (Pre-release Testing)
- **Added:** PWA (Progressive Web App) support for mobile users.
- **Added:** Enhanced Admin UI and advanced notification delivery logic.
- **Added:** Service visibility logic based on configuration.
- **Fixed:** Critical fixes for booking logic, API authentication, and SEO.
- **Fixed:** Database migration hanging issues and missing system migrations.
- **Infrastructure:** Application log cleanup and comprehensive Git ignore patterns.

---

## [0.6.0] - 2026-02-15
### Notifications & Data Sync
- **Changed:** Comprehensive refactor of the notification system and email delivery.
- **Fixed:** Booking error handling and master selection bug.
- **Fixed:** Removed hardcoded Telegram admin IDs (moved to config).
- **Fixed:** Django AttributeError and missing sitemap templates.

---

## [0.5.0] - 2026-02-14
### Infrastructure & Security
- **Added:** CI/CD workflows via GitHub Actions for automated deployment.
- **Added:** Test environment setup and test suite modularization.
- **Fixed:** Nginx configuration (reverse proxy, SSL headers, template substitution).
- **Fixed:** Security vulnerabilities and infrastructure issues from code review.
- **Security:** Added `.env.production` to `.gitignore`.

---

## [0.4.0] - 2026-02-13
### SEO, i18n & Architecture
- **Added:** i18n support for static content and legal views refactoring.
- **Added:** Comprehensive SEO and semantic improvements.
- **Added:** Legal pages (Privacy Policy, etc.) and enhanced navigation.
- **Changed:** Major system architecture migration and project cleanup.
- **Worker:** Updated Dockerfile and README for ARQ worker.

---

## [0.3.0] - 2026-02-12
### Core Logic: Booking System
- **Added:** Implementation of the comprehensive Booking Wizard.
- **Changed:** Refactoring of the worker system for background tasks.
- **Fixed:** Local check synchronization and template-related issues.

---

## [0.2.0] - 2026-02-10
### Prototype & Structure
- **Added:** Core site structure, base templates, and CSS architecture.
- **Changed:** Backend package renaming and module prototyping.

---

## [0.1.0] - 2026-02-08
### Foundation
- **Added:** Project initialization: `lily_website`.
- **Added:** Template snapshot transfer and activation (all modules).
