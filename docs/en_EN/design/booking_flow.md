# 📅 Booking Flow & Telegram Logic

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

---

This document describes the "Book Now" button algorithm and the messenger-based management system.

## 1. User Scenarios (Frontend Flow)

### Scenario A: "Classic Booking" (Button on Home)

The client doesn't know who they want, they need a service.

1.  **Trigger:** CTA button on the first screen.
2.  **Step 1 (Category):** Choice: Hair Salon / Nail Service.
3.  **Step 2 (Service):** Choice of specific procedure (e.g., "Bob Cut").
    *   *System:* Pulls `duration` and price.
4.  **Step 3 (Master):**
    *   Option A: "Any available master" (maximum slots).
    *   Option B: Choice of a specific specialist from the list (those linked to this service).
5.  **Step 4 (Date and Time):** Calendar shows ONLY those slots where the selected service "fits".
6.  **Final:** Enter Name and Phone -> SMS code (optional) -> "Thank you".

### Scenario B: "Personal Booking" (From Master's Page)

The client wants exactly this person.

1.  **Trigger:** Button "Book with [Name]" in master's profile.
2.  **Step 1:** Master is already fixed.
3.  **Step 2:** Service list is filtered (show only what this master does).
4.  **Next:** Steps 3-6 as in Scenario A.

---

## 2. "Time Tetris" Algorithm (Backend Logic)

The system does not offer rigid slots (10:00, 11:00). It calculates them dynamically.

*   **Input Data:**
    *   `Service Duration`: 90 min.
    *   `Master Schedule`: Free from 12:00 to 16:00.
*   **Logic:**
    1.  Client selects service (90 min).
    2.  System scans master's schedule.
    3.  It finds "windows" >= 90 minutes.
    4.  Displays start options to client: 12:00, 12:30, 13:00, 13:30 (later is impossible, won't finish by 16:00).
*   **Buffer Time:** Automatically add +15 minutes after each service for cleaning/rest.

---

## 3. Telegram Admin (Management)

Instead of a complex Admin Panel on the site, all management happens via Telegram bot.

### Roles

*   **Owner (Superuser):** Sees everything, can cancel any bookings, change schedule.
*   **Master:** Sees only their own bookings.

### Notifications (Events)

1.  **New Booking:**
    *   *Message:* "🔥 New booking! Client: Anna (+49...). Service: Haircut. Time: Tomorrow 14:00."
    *   *Buttons:* [Confirm] | [Decline] | [Contact].
2.  **Reminder (Morning):**
    *   "Good morning! You have 4 clients today. First one at 10:00."

---

## 4. Waitlist

*If no free spots:*

1.  Client sees message: "Unfortunately, no spots on this date".
2.  Button appears: **"Notify if a spot opens up"**.
3.  Client leaves phone number.
4.  If someone cancels booking -> Admin gets alert: "Window opened! There are 2 people in waitlist, call them".

---

## 5. Technical Database Requirements

To implement this logic, the data model (`models.py`) must strictly contain:

*   `Service.duration_minutes` (Integer).
*   `Specialist.telegram_id` (For sending notifications).
*   `Booking.status` (New / Confirmed / Cancelled).
