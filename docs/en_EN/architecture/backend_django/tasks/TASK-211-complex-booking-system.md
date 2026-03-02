# TASK-211: Complex Booking System (Combo / Multi-Service)

**Status:** 📝 Design Phase
**Priority:** High
**Domain:** Booking System
**Estimate:** 12-16 hours

---

## Description

Refactor the booking flow to allow users to book multiple services in a single session, ensuring a continuous "chain of time" (6-7 hours if needed). The system must calculate availability across masters to find back-to-back slots for the entire selected "complex".

### Core Requirements

1.  **Selection Step (Transformer)**: New UI button at the start of the wizard: "Complex Booking".
2.  **Service Basket**: Users pick multiple services. The total duration is calculated in real-time.
3.  **Smart Chain Calculation**: Find time slots where $Service_1, Service_2, \dots, Service_n$ can be performed sequentially without significant gaps.
4.  **Master Logic**:
    *   **Single-Master preferred**: Try to find one master who can perform all selected services.
    *   **Master-Relay fallback**: If no single master is available, find a sequence (e.g., Master A for Nails → Master B for Lashes) with < 15min gap between them.
5.  **Unified Booking**: Create multiple appointment records linked together (linked by a `combo_id`).

## Acceptance Criteria

- [ ] "Complex Booking" button added to `wizard.html`
- [ ] Multi-service selection UI (Cart/Basket)
- [ ] Logic to calculate total duration and total price
- [ ] `ComboSlotFinderService` implemented to find continuous free windows
- [ ] Validation: Ensure the "chain" doesn't cross the end of the working day
- [ ] Unified confirmation page showing all selected services and masters
- [ ] Database support for linked appointments (parent/combo id)

## Technical Architecture Deep Dive

### 1. Slot Chaining Algorithm (The "Transformer")

The core challenge is finding a continuous block of time $T_{total} = \sum D_i$. Currently, `SlotService` finds gaps for a single $D$.
For a complex, we need a "Relay" approach:

1.  **Input:** `[Service_A, Service_B, Service_C]`
2.  **Step 1:** Find all masters who can do $\{A, B, C\}$.
3.  **Step 2:** Search for a window $W$ on date $D$ where:
    *   $\text{Master}_1$ is free from $T_0$ to $T_0 + D_A$.
    *   $\text{Master}_2$ is free from $T_0 + D_A$ to $T_0 + D_A + D_B$.
    *   $\text{Master}_3$ is free from $T_0 + D_A + D_B$ to $T_{total}$.
    *   *Constraint:* $\text{Master}_1, \text{Master}_2, \text{Master}_3$ can be the same person (preferred) or different people. If different, we allow a maximum buffer of 15 minutes between services.

### 2. UI/UX Flow (HTMX & Liquid)

- **Entry Point:** A prominent "Complex Booking" button on the first step of the wizard.
- **Service Selector:** A new HTMX partial `_combo_selector.html` that allows multiple service selection (instead of the standard radio-style single select).
- **Live Counter:** An Alpine.js or HTMX-reactive "Total Duration" and "Total Price" bar at the bottom.
- **Smart Calendar:** The calendar only enables days where at least one continuous "link" of services is possible.

### 3. Database & Order Logic

To maintain system integrity, a complex booking will create $N$ separate `Appointment` records.
- **Linking:** All records share a `parent_combo_id` (UUID).
- **Atomic Deletion:** If an admin cancels one part of the combo, the system should prompt to "Cancel entire complex?".
- **Source Attribute:** Marked as `source="website_complex"`.

## Dependencies

- **Requires:** TASK-204 (HTMX Booking Flow)
- **Requires:** TASK-203 (Slot calculation basics)
- **Blocks:** Loyalty system (combo bookings might have special discounts)

## Testing Checklist

- [ ] Select 3 services (total 4h) -> verify only slots with 4h free space appear.
- [ ] Verify "any master" logic for each service in the chain.
- [ ] Test boundaries (near closing time).
- [ ] Ensure cancelling one part of a combo alerts the admin about the whole chain.

## Future Enhancements
- Visual "timeline" of the booking in the confirmation step.
- "Expert Suggester": Pre-packaged complexes (e.g. "Full Day Glow-up").
