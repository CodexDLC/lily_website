# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

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
