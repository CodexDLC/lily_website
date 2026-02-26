# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

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
