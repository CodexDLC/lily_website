# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

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

## [1.6.0] - 2026-02-27
### Added
- **Cabinet:** Implemented QR-based appointment finalization for masters.
- **Analytics:** Fixed GA4 tracking logic for better event reporting.

### Changed / Refactored
- **Security:** Enhanced security and cleaned up imports in notification services.
- **Documentation:** General documentation updates and improvements.

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
