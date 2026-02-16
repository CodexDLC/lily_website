# Analytics & Cookie Consent Implementation Guide

This document outlines the implementation of Google Analytics 4 (GA4), Google Tag Manager (GTM), and a GDPR-compliant Cookie Consent Banner for the LILY Beauty Salon website.

## 1. Overview

The goal is to integrate analytics tools while strictly adhering to EU privacy regulations (GDPR/DSGVO). We use **Google Consent Mode v2** to manage how Google tags behave based on user consent.

### Key Components:
1.  **Backend (`SiteSettings`)**: Stores GA4 and GTM IDs, editable via Django Admin.
2.  **Frontend (Templates)**:
    *   `includes/_analytics_head.html`: Initializes Consent Mode (default: denied) and loads GA4/GTM scripts.
    *   `includes/_analytics_body.html`: GTM `<noscript>` fallback.
    *   `includes/_cookie_consent.html`: The visual banner for user interaction.
3.  **Logic (JS)**: Handles user choices (Accept/Reject) and updates Google Consent state.

---

## 2. Backend Configuration

### Model: `SiteSettings`
Located in: `src/backend_django/features/system/models/site_settings.py`

New fields added for dynamic configuration:
*   `google_analytics_id`: Stores the GA4 Measurement ID (e.g., `G-XXXXXXXXXX`).
*   `google_tag_manager_id`: Stores the GTM Container ID (e.g., `GTM-XXXXXXX`).

### Admin Interface
Located in: `src/backend_django/features/system/admin.py`

A new fieldset **"Analytics & Marketing"** is available in the Site Settings admin page to easily update these IDs without code changes.

---

## 3. Frontend Implementation

### A. Consent Mode v2 (The "Brain")
Before loading any analytics script, we must define the default consent state. This is done in `<head>` **before** GTM/GA4 snippets.

**Default State:**
```javascript
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}

// 1. Define default consent (DENIED by default)
gtag('consent', 'default', {
  'ad_storage': 'denied',
  'ad_user_data': 'denied',
  'ad_personalization': 'denied',
  'analytics_storage': 'denied',
  'wait_for_update': 500
});

// 2. Load scripts (GA4 / GTM)
// ... scripts load here but will NOT set cookies until consent is granted ...
```

### B. The Cookie Banner (`_cookie_consent.html`)
A fixed banner at the bottom of the screen (or modal) with the following options:
*   **Accept All**: Grants full consent (`granted`).
*   **Reject All**: Keeps default consent (`denied`).
*   **Settings (Optional)**: Granular control (Marketing vs Analytics).

**Design:**
*   Styled with Tailwind CSS to match LILY branding.
*   Responsive (mobile-friendly).
*   Includes a link to the Privacy Policy (`/privacy-policy/`).

### C. JavaScript Logic (`cookie-consent.js`)
Handles the interaction:
1.  Checks `localStorage` for saved consent.
2.  If no consent found -> Shows banner.
3.  On "Accept":
    *   Updates Google Consent: `gtag('consent', 'update', { ... 'granted' ... })`.
    *   Saves to `localStorage`.
    *   Pushes `{'event': 'cookie_consent_update'}` to DataLayer (for GTM triggers).
    *   Hides banner.
4.  On "Reject":
    *   Saves rejection to `localStorage`.
    *   Hides banner.
    *   Google tags continue running in "restricted" mode (no cookies, ping-only).

---

## 4. How to Use

### 1. Get your IDs
*   **GA4**: Go to Google Analytics -> Admin -> Data Streams -> Copy **Measurement ID** (`G-XXXXXXXXXX`).
*   **GTM (Optional)**: Go to GTM -> Admin -> Copy **Container ID** (`GTM-XXXXXXX`).

### 2. Configure in Admin
1.  Log in to `/admin/`.
2.  Go to **System & Users** -> **Site Settings**.
3.  Scroll to **Analytics & Marketing**.
4.  Paste your IDs.
5.  Save.

### 3. Verify
1.  Open the website in Incognito mode.
2.  You should see the Cookie Banner.
3.  Open Developer Tools -> Application -> Cookies.
    *   **Before Accept**: No `_ga` or `_gid` cookies should be present.
    *   **After Accept**: `_ga` cookies should appear.

---

## 5. Technical Details (For Developers)

### File Structure
*   `src/backend_django/features/system/models/site_settings.py`: Database schema.
*   `src/backend_django/templates/includes/_analytics_head.html`: Head scripts.
*   `src/backend_django/templates/includes/_analytics_body.html`: Body scripts.
*   `src/backend_django/templates/includes/_cookie_consent.html`: UI component.
*   `src/backend_django/static/js/cookie-consent.js`: Logic.

### GTM Triggers (If using GTM)
If you use GTM, create a Custom Event trigger named `cookie_consent_update` to fire tags that require consent (e.g., Facebook Pixel) only *after* the user accepts.

### GDPR Compliance
*   **Explicit Consent**: Cookies are not set until the user clicks "Accept".
*   **Granular Control**: Users can choose specific categories (if implemented).
*   **Revocable**: Users can change their mind (a "Cookie Settings" link in the footer is recommended).
*   **Log**: Google Consent Mode handles the signaling to Google services automatically.
