# 💡 Future Concepts & Ideas

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

---

This document serves as an "idea bank" (Backlog) for future project development stages. Hypotheses requiring verification or content are recorded here.

## 1. "Before/After" Gallery in Services (Service Gallery)

**Concept:**
Implement a block with work examples directly on the specific service page (e.g., `hair.html`), right after the price list or "Book Now" button.

### Why (Value):

*   **Trust:** Client sees real results, not stock photos.
*   **SEO:** Unique images with alt-tags boost ranking.
*   **Conversion:** Visual confirmation of quality removes fear before booking.

### Implementation:

*   **UI:** Horizontal carousel (Swipe) on mobile, Grid (3-4 photos) on desktop.
*   **Content:** Photos must be in a unified style (lighting, angle). Ideally — "Before/After" format with a slider.
*   **Complexity:** ⭐⭐ (Medium). Requires photo selection and slider layout.

---

## 2. Extended Master Profile (Master Page)

**Concept:**
Full-fledged personal page (or expanded block) for each top master. Structure repeats the premium Owner block (Director).

### Structure (Layout):

1.  **Info Block (Top):**
    *   **Right (or Left):** Large professional photo of the master.
    *   **Text:** Biography, specialization, philosophy, work experience.
    *   **CTA:** Personal button "Book with [Name]".
2.  **Portfolio (Bottom):**
    *   Grid of best works of this specific master (6-9 photos).
    *   Located immediately below the description.

### Why (Value):

*   **Personal Contact:** Client chooses a person, not a "salon".
*   **Navigation:** Direct path to booking a specific specialist without extra clicks.

---

## 3. Social Media Hub & QR (Communication)

**Concept:**
Replace simple Instagram link with a "Contact Us" block combining all messengers (WhatsApp, Telegram, Viber, Instagram).

### Implementation:

*   **Desktop:** On hover over WhatsApp icon, a beautiful QR code pops up for phone scanning.
*   **Mobile:** On click, app opens immediately (Deep Link: `wa.me/...`, `t.me/...`).
*   **Design:** Stylized gold QR codes on dark background.

### Why (Value):

*   **Convenience:** Easier for client to write than call.
*   **Omnichannel:** Coverage of all popular messengers.

---

## 4. Smart Retention (Auto-Return Clients)

**Concept:**
System automatically tracks last visit date and sends a reminder when it's time for a repeat procedure.

### Logic (Algorithm):

1.  **Trigger:** Visit date + Service cycle (Manicure = 3 weeks, Haircut = 6 weeks).
2.  **Channel:** Email or Telegram bot.
3.  **Message:** "Anna, time to refresh your manicure! Maria has free windows next week: Tue 14:00, Wed 10:00".

### Why (Value):

*   **LTV (Lifetime Value):** Clients visit more often and don't forget about the salon.
*   **Care:** Client feels personal attention.
*   **Load:** Filling empty slots in advance.

---

## 5. Priority Assessment (Impact/Effort)

| Feature | Value | Effort | Verdict |
| :--- | :---: | :---: | :--- |
| **Service Gallery** | 🔥 High | Medium | **Must Have** (Implement first) |
| **Master Profile** | ⭐️ High | High | **Approved** (Requires content and photoshoot) |
| **Social QR Hub** | 💬 Medium | Low | **Nice to Have** (Easy to implement) |
| **Smart Retention** | 💰 Very High | High | **Strategic Goal** (Requires CRM/Backend) |

---

## 6. Technical Notes

*   To implement galleries, a JavaScript library (e.g., `Swiper.js` or `Splide`) or native CSS Scroll Snap will be required.
*   Photos must be optimized (WebP) and have Lazy Loading.
