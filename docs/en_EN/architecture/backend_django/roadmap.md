# 🗺️ Django Backend Development Roadmap

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../README.md)

---

This roadmap organizes development tasks by **domain** (feature area). It reflects the current state of the project after the implementation of the core booking system.

## 📊 Overall Progress

| Domain | Status | Progress | Priority |
|:---|:---:|:---:|:---:|
| **[✅ Booking System Core](#-booking-system-core)** | ✅ Done | 100% | Critical |
| **[✅ Booking Wizard UI (HTMX)](#-booking-wizard-ui-htmx)** | ✅ Done | 100% | Critical |
| **[🔄 Advanced Booking (Combo)](#-advanced-booking-combo)** | 📝 Design | 10% | High |
| **[🔄 Notifications & Background Tasks](#-notifications--background-tasks)** | 🔄 In Progress | 20% | High |
| **[✅ QR Finalization System](#-qr-finalization-system)** | ✅ Done | 100% | Medium |
| **[🎨 Frontend & Design](#-frontend--design)** | ✅ Done | 90% | Critical |
| **[📄 Content Pages](#-content-pages)** | ✅ Done | 95% | Critical |
| **[✅ Localization (i18n)](#-localization-i18n)** | ✅ Done | 90% | High |
| **[✅ SEO & Analytics](#-seo--analytics)** | ✅ Done | 100% | High |
| **[⚙️ Admin & Backend](#️-admin--backend)** | 🔄 In Progress | 80% | Medium |

---

## 🔄 Advanced Booking (Combo)

**Goal:** Allow users to book multiple services in one session with continuous time slots.
**Status:** 📝 10% - Design specification in progress.

### Tasks
- [ ] **[TASK-211](./tasks/TASK-211-complex-booking-system.md):** Implement Multi-Service "Complex" Booking.
- [ ] Create "Combo Transformer" service for slot chaining.
- [ ] Support multi-master relay for complex bookings.
- [ ] Implement combo discount logic.

---

## ✅ Booking System Core

**Goal:** Solid foundation with Master, Client (Ghost), and Appointment models.
**Status:** ✅ 100% - Core models and services are implemented and in use.

### Tasks
- [x] **[TASK-101](./tasks/archived/TASK-101-master-model.md):** Create `Master` model.
- [x] **[TASK-301](./tasks/archived/TASK-301-client-model.md):** Create `Client` model with Ghost User pattern.
- [x] **[TASK-201](./tasks/archived/TASK-201-appointment-model.md):** Create `Appointment` model.
- [x] Implement `ClientService` for ghost user management.
- [x] Implement `BookingService` for appointment creation.
- [x] Refactor services to be stateless and use static methods.
- [x] Optimize database queries in services (e.g., using `Q` objects).

---

## ✅ Booking Wizard UI (HTMX)

**Goal:** Dynamic, multi-step booking flow for a seamless user experience.
**Status:** ✅ 100% - The booking wizard is fully functional.

### Tasks
- [x] **[TASK-204](./tasks/archived/TASK-204-htmx-booking-flow.md):** Implement HTMX-based wizard.
- [x] Implement `BookingState` DTO for type-safe session management.
- [x] Implement `BookingSessionService` to handle the DTO.
- [x] Refactor view, steps, and selectors to use the `BookingState` DTO.
- [x] Support Service-first booking path.
- [x] Ensure the flow is responsive and works on mobile.

---

## 🔄 Notifications & Background Tasks

**Goal:** Inform users and admins about booking status via Email and background tasks.
**Status:** 20% - Basic structure exists. Background tasks (ARQ) are not implemented.

### Tasks
- [ ] **[ARQ]** Implement ARQ client for asynchronous task processing.
- [ ] **[ARQ]** Create a background task for sending booking confirmation emails.
- [ ] **[ARQ]** Create a background task for sending appointment reminders (e.g., 24 hours before).
- [x] **[Email]** Basic email notification functions exist in `services/notifications.py`.
- [ ] Create and translate all required email templates (`booking_approved`, `booking_rejected`, etc.).

---

## ✅ QR Finalization System

**Goal:** Secure appointment price adjustment via QR scanning by administrators.
**Status:** ✅ 100% - Integrated into Admin Cabinet.

### Tasks
- [x] **[TASK-205](./tasks/archived/TASK-205-qr-finalization-system.md):** Implement Admin-only QR Price Adjustment.
- [x] Create `AppointmentPriceEditView` with token validation.
- [x] Add `price_actual` field to `Appointment` model.
- [ ] Connect with `tools/media/qr_style.py` for branded QR generation.

---
## 📄 Content Pages

**Goal:** All essential pages with SEO optimization.
**Status:** 95% - Main pages are done, some content/translations may be pending.

### Tasks
- [x] Home page, Services overview, Service detail pages.
- [x] Team page (owner + masters list).
- [x] Legal pages (Impressum, Datenschutz).
- [x] Error pages (404, 500).
- [ ] Contacts page with map and contact form.
- [ ] Complete all translations.

---
## 🎨 Frontend & Design

**Goal:** Professional, responsive design ready for production.
**Status:** 90% - Core CSS and structure are complete. Minor JS tweaks and optimizations may be needed.

### Tasks
- [x] Modular CSS structure and compilation system.
- [x] 5-breakpoint responsive system.
- [x] WebP image conversion.
- [x] Base layout with header/footer.
- [ ] Add mobile menu toggle (burger menu).
- [ ] Image lazy loading.
- [ ] Optimize Lighthouse scores (Performance 90+).

---
## ✅ Localization (i18n)

**Goal:** Full 4-language support (DE, RU, UK, EN).
**Status:** ✅ Done | 90% - Technical setup is done, content translation is in progress.

### Tasks
- [x] Configure `django-modeltranslation`.
- [x] Add translation tags to templates.
- [ ] **[TASK-401]** Translate all static text.
- [ ] **[TASK-402]** Add language switcher to header.
- [ ] **[TASK-403]** Configure URL localization (`/de/`, `/ru/`, etc.).
- [ ] Final localization audit and bug fixing (UI/UX tweaks).

---
## ✅ SEO & Analytics

**Goal:** Optimize for search engines and implement tracking.
**Status:** ✅ 100% - SEO structure, JSON-LD, and Analytics are implemented.

### Tasks
- [x] Add SEO meta tags to templates via mixins.
- [x] Create `sitemap.xml` and `robots.txt`.
- [x] **[TASK-601]** Add JSON-LD structured data (LocalBusiness, Service, OfferCatalog).
- [x] **[TASK-603]** Add Google Analytics / Matomo integration.

---
## ⚙️ Admin & Backend

**Goal:** Efficient admin interface for content management.
**Status:** 60% - Basic admin for core models is configured. Advanced features are pending.

### Tasks
- [x] Configure Django Admin with custom styling (Unfold).
- [x] Add admin for `Category`, `Service`, `Master`, `Client`, `Appointment`.
- [x] Use `modeltranslation` in admin.
- [x] **[TASK-701]** Customize admin dashboard with statistics.
- [x] **[TASK-210](./tasks/archived/TASK-210-contact-requests-cabinet.md):** Implement Contact Requests management in Cabinet.
- [ ] **[TASK-703]** Implement image upload previews in forms.
- [ ] **[TASK-704]** Add inline editing for `MasterPortfolio` and `MasterCertificate` in `MasterAdmin`.
