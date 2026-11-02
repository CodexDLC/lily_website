---
name: lily-cabinet-feature-change
description: Maintain Lily staff/client cabinet screens, active-module context and navigation integration. Use for cabinet work; exclude public marketing pages and Django admin.
---

# Lily Cabinet Changes

Project screen code lives in `src/lily_backend/cabinet/views/`, `services/` and `templates/cabinet/` beneath that app. Business models and workflows may belong to a feature. Preserve existing centralized screens instead of relocating them merely to follow a generic layout preference.

For navigation, module registration or startup changes read [navigation wiring](references/navigation.md). For a visual-only change, reuse the existing cabinet base/components and Bootstrap Icons without loading unrelated registration details.

Preserve the active module and authorization of the existing screen. `BaseBookingView.dispatch()` in `src/lily_backend/cabinet/views/booking.py` sets `request.cabinet_module = "booking"`; reuse the relevant base/helper for module pages. Do not infer that every action endpoint must render a sidebar.

Cabinet page services also assemble presentation context. Follow [read/write paths](../lily-selector-service-discipline/SKILL.md) when changing data or actions. Booking's page service delegates to its feature workflow; do not duplicate booking rules in the screen.

Keep public and cabinet styling separate. For source/bundle edits use [static assets](../lily-static-assets/SKILL.md). Some templates/assets are library-owned: `tests/lily_backend/unit/test_cabinet_library_assets.py` asserts that chart/donut widgets, `cabinet.js` and Alpine resolve from `codex_django`. Do not shadow them with copied project files as an incidental fix.

For changed behavior, verify the affected auth/POST/context path; for navigation verify the active module and registered destinations. Existing evidence includes `tests/lily_backend/unit/test_cabinet_context.py`, `test_booking_cabinet.py` in the same directory, and `tests/lily_backend/integration/cabinet/`. Visual changes additionally need rendered desktop/mobile inspection.
