# 🗺️ Content Strategy & Localization (Content Map)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

---

## 1. Internationalization (i18n)

The system is designed based on `Django Translation`. We support 4 languages.

*   **Languages:**
    *   **DE (German):** Mandatory for legal pages (Impressum, AGB) and local audience.
    *   **RU (Russian) / UA (Ukrainian):** Potentially main communication languages (depends on target audience).
    *   **EN (English):** Additional.
*   **Technical Implementation:**
    *   All static text (menu, buttons, headings) is wrapped in translation tags `&#123;% trans "Text" %&#125;`.
    *   Dynamic content (service descriptions, master bios) is stored in the database with duplicated fields (e.g., `description_de`, `description_ru`).

## 2. "Clean Media" Rule (No Embedded Text)

*   **Principle:** Text is never "baked" into images (JPG/PNG).
*   **Why:** So text can be automatically translated when switching languages, indexed by search engines, and resized on mobile.
*   **Implementation:**
    *   Logo (header background) — used as a substrate. Text "Beauty Salon" and navigation are laid out over it with HTML tags.
    *   Service/Master cards — photo is clean, captions are in a separate `div` block over or below.

## 3. Copywriting Structure

### A. Header and Hero

*   **Slogan:** Short, emotional.
    *   *Example:* "The Art of Your Beauty" (EN) / "Die Kunst Ihrer Schönheit" (DE).
*   **CTA Button:** Action verb. "Book Now" / "Termin buchen".

### B. "Trust" Block

*   Text heading above the logo carousel.
*   *Essence:* Explanation of what these logos are (Schools, Partners, Cosmetics used).

### C. Footer (Legal)

*   **Important:** In Germany, `Impressum` (Imprint) and `Datenschutz` (Privacy) sections must be available in German at all times, even if the site is switched to Russian.

## 4. SEO (Search Engine Optimization)

*   Texts must contain geo-targeting (Köthen, Germany) in H1/H2 headings in all languages.

---

## 5. TECHNICAL SEO & GEO (Site Passport for AI)

To ensure search engines and neural networks (Gemini, ChatGPT, Siri) understand we are in Köthen and provide services, we implement 3 levels of markup.

### A. GEO Meta Tags

Written in `<head>`. Strictly bind the site to coordinates so we rank in "Google Maps" and local search results.

```html
<meta name="geo.region" content="DE-ST" />
<meta name="geo.placename" content="Köthen (Anhalt)" />
<meta name="geo.position" content="51.75;11.96" />
<meta name="ICBM" content="51.75, 11.96" />
```

### B. Open Graph (For Social Media)

So that when sending a link in WhatsApp/Telegram, there is a nice preview image, not an empty square.

```html
<meta property="og:type" content="business.business">
<meta property="og:title" content="LILY Beauty Salon - Friseur in Köthen">
<meta property="og:url" content="https://lily-salon.de">
<meta property="og:image" content="https://lily-salon.de/static/img/social-share.jpg">
<meta property="business:contact_data:street_address" content="[Salon Address]">
<meta property="business:contact_data:locality" content="Köthen">
<meta property="business:contact_data:country_name" content="Germany">
```

### C. JSON-LD Schema (Main for AI)

This is hidden code that "feeds" the business structure to robots. AI reads exactly this. We use the `BeautySalon` schema (child of `LocalBusiness`).

**What we include in JSON:**

*   `@type`: "BeautySalon"
*   `name`: "LILY Beauty Salon"
*   `image`: Link to logo/facade.
*   `priceRange`: "€€" (Medium/High).
*   `address`: Full address with zip code.
*   `telephone`: Clickable number.
*   `openingHours`: Schedule (so Siri knows if we are open now).
*   `hasMap`: Link to Google Maps CID.

### D. Hreflang (For Languages)

So Google doesn't confuse Russian and German versions and doesn't consider them duplicates.

```html
<link rel="alternate" hreflang="de" href="https://site.de/" />
<link rel="alternate" hreflang="ru" href="https://site.de/ru/" />
<link rel="alternate" hreflang="uk" href="https://site.de/ua/" />
<link rel="alternate" hreflang="x-default" href="https://site.de/" />
```
