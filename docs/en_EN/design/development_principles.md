# LILY Beauty Salon Technical Knowledge Base & Development Principles

This document is the primary technical standard of the project. It contains comprehensive information on architecture, SEO, localization, and performance, essential for developing and supporting the site.

---

## 1. Localization & i18n (Semantic Key Architecture)

We use a hybrid system: interface strings in `.po` files and marketing content in the database.

### 1.1. Key System (UI)
Accessed via `{% trans "key" %}`. **Never** insert raw text directly into the `trans` tag.

#### Group: Navigation (`nav_`)
| Key | Context |
| :--- | :--- |
| `nav_main_home` | Home Page |
| `nav_main_services` | Services |
| `nav_main_team` | Team |
| `nav_main_contacts` | Contacts |
| `nav_footer_all_contacts` | "All Contacts" footer link |
| `nav_legal_impressum` | Impressum |
| `nav_legal_privacy` | Datenschutz |

#### Group: Buttons & Actions (`btn_`)
| Key | Context |
| :--- | :--- |
| `btn_cta_booking` | Main Booking Button |
| `btn_action_more` | "Read More" |
| `btn_form_submit` | Form Submission |
| `btn_form_cancel` | Cancel |
| `btn_ui_toggle_footer` | Footer Toggle |

#### Group: Services (`service_`)
| Key | Category/Service |
| :--- | :--- |
| `service_cat_hair` | Hair |
| `service_cat_nails` | Nails |
| `service_item_manicure` | Manicure |
| `service_item_coloring` | Coloring |

### 1.2. Database Content (StaticTranslation)
For frequently changing texts (Hero sections, service descriptions), the `StaticTranslation` model is used.
- **Template Access**: `{{ content.home_hero_title }}`.
- **Language Support**: Fields `text_de`, `text_en`, `text_ru`, `text_uk` (via `modeltranslation`).

---

## 2. SEO & AI Optimization (AIO)

The site is designed for human search (Google) and machine search (LLM/AI).

### 2.1. AI-Context (Special Purpose)
`llms_*.txt` files provide AI agents (ChatGPT, Perplexity) with precise information.
- **Location**: `src/backend_django/templates/llms_[lang].txt`
- **Content**: Service structure, FAQ, payment methods, parking, etc.

### 2.2. Technical SEO & Sitemap
- **Dynamic Sitemap**: XML is generated via `core/sitemaps.py`. Includes dynamic service pages.
- **Hreflang**: Automatic generation in `includes/_hreflang_tags.html`.
- **Canonicals**: Always point to the primary domain set in `CANONICAL_DOMAIN`.

### 2.3. Structured Data (JSON-LD)
The `_schema_local_business.html` file implements the `LocalBusiness` schema with support for:
- **OpeningHours**: Dynamically from the DB.
- **GeoCoordinates**: For maps.
- **OfferCatalog**: Deep nesting of categories and services for Google Search.

---

## 3. Performance & Build

### 3.1. Load Optimization (Render-Blocking)
- **Critical CSS**: Inlined in the `<head>` tag via `_critical_css.html`. Contains header and Hero section styles.
- **Async JS/CSS**: Main files are loaded with `defer` or via preload polyfills.
- **Fetch Priority**: Critical images (logo, first banner) have the `fetchpriority="high"` attribute.

### 3.2. Images (Media)
- **WebP**: Automatic conversion of all uploads.
- **Lazy Loading**: For all images below the fold.

### 3.3. HTMX Integration
Used for:
- Dynamic service filters.
- Step-by-step booking wizard (`booking_wizard`).
- Content updates without full page reloads (via `hx-target`).

---

## 4. Configuration (SiteSettings)
Central control panel in Django Admin:
- **Socials**: Links to Instagram, WhatsApp, Facebook.
- **Analytics**: GA4 and GTM containers.
- **Service Data**: Price thresholds, working hours, coordinates.
