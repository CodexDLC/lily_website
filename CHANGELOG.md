# Changelog

All notable changes to the **Lily Website** project will be documented in this file.

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
