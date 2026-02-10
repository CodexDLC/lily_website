# 🗺️ Django Backend Development Roadmap

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../README.md)

---

This roadmap organizes development tasks by **domain** (feature area). Each domain contains a checklist of tasks with links to detailed task documents in the `tasks/` folder.

## 📊 Overall Progress

**MVP Definition:** Fully functional SEO-optimized landing page with booking form and admin approval flow.

| Domain | Status | Progress | Priority | MVP? |
|:---|:---:|:---:|:---:|:---:|
| **[🎨 Frontend & Design](#-frontend--design)** | ✅ In Progress | 70% | Critical | ✅ YES |
| **[📄 Content Pages](#-content-pages-mvp)** | 🔄 In Progress | 80% | Critical | ✅ YES |
| **[📅 Booking Form (MVP)](#-booking-form-mvp)** | 📝 Ready | 0% | Critical | ✅ YES |
| **[📧 Notifications](#-notifications-mvp)** | 📝 Ready | 0% | Critical | ✅ YES |
| **[🌐 Localization (i18n)](#-localization-i18n)** | 🔄 In Progress | 40% | High | ✅ YES |
| **[🔍 SEO & Analytics](#-seo--analytics)** | 🔄 In Progress | 30% | High | ✅ YES |
| **[⚙️ Admin & Backend](#️-admin--backend)** | 🔄 In Progress | 50% | Medium | ✅ YES |
| **[👥 Master Profiles](#-master-profiles-post-mvp)** | 📝 Design | 10% | Medium | ❌ Post-MVP |
| **[👤 Ghost User System](#-ghost-user-system-post-mvp)** | 📝 Design | 5% | Medium | ❌ Post-MVP |
| **[🔐 QR Finalization](#-qr-finalization-post-mvp)** | 📝 Design | 5% | Low | ❌ Future |
| **[📱 Advanced Bot Features](#-advanced-bot-features-post-mvp)** | ⏳ Planned | 0% | Low | ❌ Future |

---

## 🎨 Frontend & Design

**Goal:** Professional, responsive design ready for production.

### MVP Tasks (Critical for Launch)

- [x] Create modular CSS structure (base/, components/, pages/, adaptive/)
- [x] Implement 5-breakpoint responsive system (mobile → desktop-large)
- [x] Build CSS compilation system (`tools/css_compiler.py`)
- [x] Remove all inline styles from templates
- [x] Convert images to WebP format
- [x] Implement base layout with header/footer
- [ ] Add mobile menu toggle (burger menu)
- [ ] Smooth scroll for anchor links
- [ ] Test on real devices (iOS Safari, Android Chrome)
- [ ] Optimize lighthouse scores (Performance 90+)

### Post-MVP Tasks

- [ ] Image lazy loading
- [ ] Loading states and skeleton screens
- [ ] Animations and transitions
- [ ] Dark mode support

**Status:** 70% - Core done, minor JS tweaks needed.

---

## 📄 Content Pages (MVP)

**Goal:** All essential pages with SEO optimization.

### MVP Tasks (Critical for Launch)

- [x] Home page with hero and services bento grid
- [x] Services overview page with price list
- [x] Service detail pages (dynamic from DB)
- [x] Team page (owner + masters list)
- [ ] Contacts page with map and contact form
- [x] Legal pages (Impressum, Datenschutz)
- [x] Error pages (404, 500)
- [ ] Complete German translations (all pages)
- [ ] Add Open Graph images for social sharing
- [ ] Test all internal links

### Post-MVP Tasks

- [ ] Master detail pages (individual profiles)
- [ ] Blog/News section
- [ ] FAQ page
- [ ] Before/After gallery

**Status:** 80% - Main pages done, translations in progress.

---

## 📅 Booking Form (MVP)

**Goal:** Simple booking request form with owner approval.

### MVP Tasks (Critical for Launch)

- [ ] **[TASK-MVP-001](./tasks/TASK-MVP-001-simple-booking-form.md)** Create `BookingRequest` model
- [ ] Build booking form UI (name, phone, service, date/time, comment)
- [ ] Form validation (required fields, phone format)
- [ ] Success page after submission
- [ ] Admin interface for booking requests

**Status:** 0% - Task documented, ready to implement.

---

## 📧 Notifications (MVP)

**Goal:** Email and Telegram notifications for booking flow.

### MVP Tasks (Critical for Launch)

- [ ] Configure email backend (SMTP)
- [ ] Email to owner on new booking request
- [ ] Telegram notification to owner with approve/reject buttons
- [ ] Auto-reply email to client ("We'll contact you")
- [ ] Approval email to client
- [ ] Rejection email to client (with reason)
- [ ] Create email templates (DE, RU, UK, EN)

### Post-MVP Tasks

- [ ] SMS notifications (Twilio)
- [ ] Calendar invites (.ics files)
- [ ] Reminder notifications (24h before)

**Status:** 0% - Ready to implement after booking form.

---

## 🎯 Post-MVP Features

---

## 👥 Master Profiles (Post-MVP)

**Goal:** Individual master pages with portfolios and booking.

### Tasks

- [ ] **[TASK-101](./tasks/TASK-101-master-model.md)** Create `Master` model
- [ ] **[TASK-102]** Create `MasterPortfolio` model
- [ ] **[TASK-103]** Create `MasterCertificate` model
- [ ] Master detail page templates
- [ ] Portfolio bento grid
- [ ] Diploma carousel (horizontal swiper)
- [ ] "Book with [Master]" CTA integration

**Status:** 10% - Design done, implementation pending.

---

## 👤 Ghost User System (Post-MVP)

**Goal:** Automatic client creation and progressive profiling.

### Tasks

- [ ] **[TASK-301](./tasks/TASK-301-client-model.md)** Create `Client` model
- [ ] Ghost user creation on booking
- [ ] Client matching by phone/email
- [ ] Access token system
- [ ] Account activation flow
- [ ] Personal cabinet (booking history)
- [ ] GDPR compliance (data export/deletion)

**Status:** 5% - Concept documented, ready for implementation.

---

## 🔐 QR Finalization (Future)

**Goal:** On-site appointment finalization via QR scanning.

### Tasks

- [ ] **[TASK-205](./tasks/TASK-205-qr-finalization-system.md)** QR finalization system
- [ ] Telegram Bot Mini App with QR scanner
- [ ] Price adjustment UI in bot
- [ ] Scan analytics and lead tracking
- [ ] Reports generation (Excel export)

**Status:** 5% - Full design documented, future feature.

---

## 📱 Advanced Bot Features (Future)

**Goal:** Rich bot experience beyond basic notifications.

### Tasks

- [ ] Master registration in bot (access codes)
- [ ] Master dashboard (today's appointments)
- [ ] Client booking via bot
- [ ] Appointment reminders
- [ ] Personal statistics for masters
- [ ] Owner analytics dashboard

**Status:** 0% - Future expansion.

---

## 🌐 Localization (i18n)

**Goal:** Full 4-language support (DE, RU, UK, EN).

### Tasks

- [x] Configure django-modeltranslation
- [x] Add translation tags to templates
- [ ] **[TASK-401]** Translate all static text (DE, RU, UK, EN)
- [ ] **[TASK-402]** Add language switcher to header
- [ ] **[TASK-403]** Configure URL localization (`/de/`, `/ru/`, etc.)
- [ ] **[TASK-404]** Add hreflang meta tags for SEO
- [ ] **[TASK-405]** Test RTL support (if Arabic is added later)
- [ ] **[TASK-406]** Create translation management workflow

**Status:** 40% complete - Technical setup done, translations in progress.

---

## 📱 Telegram Bot Integration

**Goal:** Connect Django booking system with Telegram Bot.

### Tasks

- [ ] **[TASK-501]** Create REST API for bot (Django Ninja)
- [ ] **[TASK-502]** Implement bot authentication (shared secret)
- [ ] **[TASK-503]** Expose booking endpoints (`/api/bot/book`, `/api/bot/cancel`)
- [ ] **[TASK-504]** Sync Client records between bot and Django
- [ ] **[TASK-505]** Build notification webhooks (bot → Django)
- [ ] **[TASK-506]** Add bot-specific fields to Client model (telegram_id)
- [ ] **[TASK-507]** Test end-to-end booking flow (bot → web)

**Status:** 0% complete - Waiting for booking system completion.

---

## 🔍 SEO & Analytics

**Goal:** Optimize for search engines and implement tracking.

### Tasks

- [x] Add SEO meta tags to templates
- [x] Implement SEO mixins for models
- [x] Create sitemap.xml and robots.txt
- [ ] **[TASK-601]** Add JSON-LD structured data (BeautySalon schema)
- [ ] **[TASK-602]** Implement Open Graph images (dynamic generation)
- [ ] **[TASK-603]** Add Google Analytics / Matomo
- [ ] **[TASK-604]** Configure Google Search Console
- [ ] **[TASK-605]** Implement breadcrumb navigation
- [ ] **[TASK-606]** Add canonical URLs
- [ ] **[TASK-607]** Optimize page load speed (lazy loading, caching)

**Status:** 30% complete - Basic SEO structure in place.

---

## ⚙️ Admin & Backend

**Goal:** Efficient admin interface for content management.

### Tasks

- [x] Configure Django Admin with custom styling
- [x] Add admin for Category, Service, ServiceGroup
- [x] Add admin for SEO, SiteSettings
- [ ] **[TASK-701]** Customize admin dashboard (statistics widget)
- [ ] **[TASK-702]** Add bulk actions for services
- [ ] **[TASK-703]** Implement image upload preview in admin
- [ ] **[TASK-704]** Add inline editing for related models
- [ ] **[TASK-705]** Create custom admin views (reports)
- [ ] **[TASK-706]** Add admin permissions for staff roles

**Status:** 50% complete - Basic admin configured, advanced features pending.

---

## 🎯 Next Milestones

### Phase 1: Foundation (Current)
- ✅ CSS architecture
- ✅ Base templates
- 🔄 i18n setup
- 🔄 SEO basics

### Phase 2: Core Features (Next 2-4 weeks)
- 📝 Master models and pages
- 📝 Client/Ghost User system
- 📝 Booking models

### Phase 3: Integration (4-8 weeks)
- ⏳ Booking flow UI
- ⏳ Notifications (SMS/Email)
- ⏳ Telegram Bot API

### Phase 4: Polish (8-12 weeks)
- ⏳ Reviews and ratings
- ⏳ Analytics dashboard
- ⏳ Performance optimization

---

## 📝 Task Document Format

Each task in `tasks/` follows this structure:

```markdown
# TASK-XXX: Task Title

**Status:** 🔄 In Progress | ✅ Done | ⏳ Blocked
**Priority:** High | Medium | Low
**Assigned:** @username (optional)
**Estimate:** X hours/days

## Description
What needs to be done and why.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Details
Implementation notes, models, views, etc.

## Dependencies
- Requires TASK-YYY to be completed first

## Related Files
- `path/to/file.py`
```

---

## 🔗 Related Documentation

- [Design System](../../design/README.md)
- [Booking Flow Concept](../../design/booking_flow.md)
- [Ghost User Concept](../../design/future_ideas.md#6-ghost-user-system-progressive-profiling)
- [Telegram Bot Roadmap](../telegram_bot/roadmap.md)
