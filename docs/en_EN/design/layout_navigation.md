# 📐 Layout, Grid & Navigation

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

---

## 1. Grid & Spacing

"Air" (whitespace) is critical for creating a premium feel. Content should not be cluttered.

### Container

*   **Desktop:** `max-width: 1200px`. Centered.
*   **Mobile:** Side padding `20px`.

### Vertical Rhythm

*   **Section Padding:** `40px - 80px`.
*   **Card Padding:** `20px`.

---

## 2. Header: "Split Header" Architecture

The site header is divided into two functional blocks for better information organization.

### A. Top Bar

Located at the very top.

*   **Background:** Semi-transparent dark (`rgba(0, 40, 35, 0.8)`) with blur (Backdrop Blur).
*   **Elements:**
    *   Address (Marktstraße 10...).
    *   Phone (+49...).
*   **Style:** Small font, Uppercase, Muted White color.

### B. Main Navigation

Located below the Top Bar.

*   **Background:** Deep Emerald (`#003831`).
*   **Logo:** Left, image `logo_lily.png`.
*   **Menu (Desktop):** Center/Right. Links: Home | Services | Team | Contacts.
    *   *Active Link:* Highlighted in gold.
*   **Mobile Menu:** "Burger" button on the right. Opens full-screen menu (Overlay).

---

## 3. Footer: "Smart Footer" Concept

A compact footer that expands on demand.

### State A: "Compact" (Default)

*   **View:** Narrow strip at the bottom of the page.
*   **Content:**
    *   Branding (LILY SALON).
    *   Copyright.
    *   Button "Open contacts and services" (with arrow down).

### State B: "Expanded"

*   **Trigger:** Click on the button or footer strip.
*   **Content:**
    *   Column 1: Contacts (Phone, Address, Instagram, QR code).
    *   Columns 2-4: Service lists by category.
*   **Effect:** Smooth expansion (Slide Down).

---

## 4. Responsive Adaptation

*   **Top Bar:** Hidden on very small screens (< 600px) to avoid clutter.
*   **Header:** Logo shrinks, menu hides in Burger.
*   **Hero:** Text and image stack in a column (Text above or below, depending on design).
*   **Bento Grid:** Transforms into a single column of cards.
