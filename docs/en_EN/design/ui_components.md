# 🧩 UI Components & Elements

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

---

## 1. Buttons

Button styles should be light and not overload the interface with "bricks".

### Primary CTA

Used for the "Book Now" action in the header and on covers.

*   **Class:** `.btn-pill`
*   **Style:** Ghost Button / Outline.
*   **Shape:** Oval (50px border-radius).
*   **Background:** Transparent.
*   **Border:** `1px solid var(--color-gold)`.
*   **Text:** Uppercase, Sans-Serif font, Gold color.
*   **Hover:** Background smoothly fills with gold, text turns dark.

### Secondary Link

For "More Details", "Profile" transitions.

*   **Style:** Text with underline.
*   **Color:** Gold or White.
*   **Decoration:** `border-bottom`.

---

## 2. Service Cards

### Type A: "Bento Card" (For Home Page)

Card for the service mosaic.

*   **Background:** Full-format image (Cover).
*   **Overlay:** Gradient from bottom to top (dark to transparent) for text readability.
*   **Content:**
    *   Heading (H3, Serif).
    *   Caption (small text, description).
    *   Arrow (decoration).
*   **Interaction:** On hover, the card floats up (`translateY`), border turns gold.

### Type B: "Service Row" (For Services Page)

Row in the price list. Minimalism.

*   **Structure:**
    *   *Left:* Service Name (DE + UA/RU).
    *   *Right:* Price (Gold, Serif) + Time (Grey).
*   **Separator:** Dotted or thin line between rows.
*   **Photos:** Absent in rows to avoid overloading the list.

---

## 3. Team Unit Card

*   **Container:** "Floating" card with dark background.
*   **Photo:** Large portrait, occupies 70-80% of height.
    *   *Effect:* Zoom photo on hover.
*   **Info Block:** Located below the photo.
    *   Name (Serif, large).
    *   Role (Sans-Serif, small, uppercase).
    *   Button "Profile" (Secondary Link).

---

## 4. Forms (Inputs)

Used on the Contacts page.

*   **Style:** "Underline only".
*   **Background:** Transparent (`rgba(255,255,255, 0.02)` for container).
*   **Border:** `1px solid rgba(255,255,255,0.3)`. On focus — Gold.
*   **Font:** White, Sans-Serif.
