---
name: lily-public-template-change
description: Change Lily visitor-facing templates and page context, including public booking rendering. Exclude cabinet screens and Django admin.
---

# Lily Public Templates

Start at `src/lily_backend/templates/`, `src/lily_backend/features/main/views/` for public content, or `src/lily_backend/features/booking/views/public/` for booking. Trace the existing URL/view/context for the requested page rather than creating a static replacement for model-backed content.

Change the template directly when the context already contains the data. For missing context follow [read/write paths](../lily-selector-service-discipline/SKILL.md); for absent stored data use [schema changes](../lily-model-schema-change/SKILL.md). Do not add domain queries or booking decisions to template markup.

Public booking rendering depends on cart, availability and commit contracts. A markup task does not authorize changing those rules. If the request actually changes slot selection or appointment creation, read [booking integration](../lily-selector-service-discipline/references/booking-integration.md).

Public styling uses `src/lily_backend/static/css/`, including `components/`, `pages/` and `adaptive/`. Keep the established Lily brand/components and public/cabinet separation. For CSS/JS changes load [static assets](../lily-static-assets/SKILL.md); never patch `app.css` by hand.

Verify the affected page at mobile and desktop sizes. Add behavior checks when route/context or booking semantics change; template-only text/style edits do not require invented backend tests. Existing booking checks live under `tests/lily_backend/integration/booking/`.
