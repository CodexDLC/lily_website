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

## 6. Ghost User System (Progressive Profiling)

**Concept:**
Implement a "frictionless registration" system where users are automatically registered as temporary "ghost" accounts during their first interaction (booking, commenting, etc.) without explicit account creation.

### How It Works:

1.  **First Booking:**
    *   User books appointment: Name: "Anna", Phone: "+491234567890"
    *   System creates `Client` record with `status='guest'` and unique `access_token`
    *   User receives SMS: "Booking confirmed. Cancel: https://salon.de/cancel/{token}"

2.  **Second Interaction (Comment):**
    *   Same user leaves a review, enters email: "anna@mail.com"
    *   System finds existing `Client` by phone and enriches data with email
    *   Comment displays as: "Anna ⭐⭐⭐⭐⭐" (shows name since we have it)

3.  **Unknown User (New Comment):**
    *   New user leaves comment with only email: "new@mail.com"
    *   System creates `Client` record with empty name
    *   Comment displays as: "Guest ⭐⭐⭐⭐" (hides email/phone for privacy)

4.  **Account Activation (Optional):**
    *   User clicks "View My History" or "Create Account"
    *   System creates Django `User` account, links to existing `Client`
    *   All past bookings, comments, and data are instantly available

### Database Structure:

```python
class Client(models.Model):
    # Identifiers (at least one required)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    name = models.CharField(max_length=255, blank=True)

    # Link to Django User (null until activation)
    user = models.OneToOneField(User, null=True, blank=True,
                                 on_delete=models.SET_NULL)

    # Access without password
    access_token = models.CharField(max_length=64, unique=True)

    # Status tracking
    status = models.CharField(max_length=20, default='guest')
    # guest → active (when user is created)

    # Marketing
    consent_marketing = models.BooleanField(default=False)
```

### Why (Value):

*   **Zero Friction:** No "Create Account" barrier - user books in 30 seconds
*   **Data Enrichment:** Each interaction adds more information automatically
*   **GDPR-Friendly:** Legitimate interest (booking) for data collection
*   **Marketing Base:** Build email/phone database organically
*   **Retroactive History:** When user activates, all past data is linked
*   **Anonymous Comments:** Can show reviews without exposing contact info

### Use Cases:

1.  **Booking System:** Client books without registration, manages via SMS link
2.  **Reviews:** Verified reviews (from actual clients) shown with names
3.  **Email Marketing:** Build subscriber list from real interactions
4.  **Loyalty Program:** Track visit history even for "guests"
5.  **Telegram Bot:** Link bot conversations to same Client record

### Implementation Notes:

*   Use `Client` model as central entity (not Django User)
*   Django `User` is created only when needed (personal cabinet, password login)
*   `access_token` allows booking management without authentication
*   Match clients by phone first (primary), then email (secondary)

---

## 7. Priority Assessment (Impact/Effort)

| Feature | Value | Effort | Verdict |
| :--- | :---: | :---: | :--- |
| **Service Gallery** | 🔥 High | Medium | **Must Have** (Implement first) |
| **Master Profile** | ⭐️ High | High | **Approved** (Requires content and photoshoot) |
| **Social QR Hub** | 💬 Medium | Low | **Nice to Have** (Easy to implement) |
| **Smart Retention** | 💰 Very High | High | **Strategic Goal** (Requires CRM/Backend) |
| **Ghost User System** | 🚀 Very High | Medium | **Core Feature** (Foundation for booking) |

---

## 8. Technical Notes

*   To implement galleries, a JavaScript library (e.g., `Swiper.js` or `Splide`) or native CSS Scroll Snap will be required.
*   Photos must be optimized (WebP) and have Lazy Loading.
*   Ghost User system requires careful phone/email validation and GDPR compliance documentation.
