---
name: lily-feature-boundary-decision
description: Choose ownership for new or cross-feature Lily behavior, models and modules. Use when placement is unclear; skip edits within an established owner.
---

# Lily Feature Boundaries

Python paths below start at `src/lily_backend/`; workers live under `src/workers/`. This is the current ownership map, not a request to relocate existing code.

| Owner | Existing responsibility and source to inspect |
| --- | --- |
| `core/` | Django settings, root URLs and runtime wiring |
| `system/models/` | Shared clients/user profiles, site settings, loyalty, email/static content and SEO |
| `features/main/models/` | Service/category/combo catalog and conflict rules; public pages in `features/main/views/` |
| `features/booking/` | Appointments/groups, masters/schedules, booking settings, provider and persistence integration |
| `features/conversations/` | Messages/replies/campaigns, imported mail and communication workflows |
| `features/notifications/` | Notification logs/recipients and operational notification views |
| `cabinet/` | Project shell/auth, centralized cabinet views, page services and templates |
| `src/workers/` (repository root) | Background execution and worker orchestration |

Service catalog data belongs to `features.main` even when used by booking or the cabinet. Client data remains in `system`. Navigation registration alone does not make `cabinet` the owner of the underlying business data.

Extend the existing owner when the request shares its domain and lifecycle. Consider a new feature for an independently owned capability; do not create one merely to give a screen its own folder, or collect unrelated workflows in `system`.

Some booking files carry scaffold/blueprint ownership markers. Check those markers before changing integration structure; their presence does not prove a planned extraction has happened. Keep project-specific rules in the established provider/persistence seams. For that work read [booking integration](../lily-selector-service-discipline/references/booking-integration.md).
