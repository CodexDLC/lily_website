---
name: lily-cabinet-feature-change
description: Load this skill when changing Lily cabinet pages, staff/client dashboard modules, booking or conversations cabinet screens, cabinet navigation, topbar/sidebar/settings_url registration, cabinet templates, or operational UI.
---

# Lily Cabinet Feature Change

Use this for `cabinet/` surfaces and feature-owned operational modules.

## Cabinet boundaries

Cabinet is operational UI. Do not mix it with public marketing templates.

Feature-owned cabinet code should stay near the owning feature when possible:

- `features.<feature>.cabinet.py` for topbar/sidebar/settings registration
- feature URLs or cabinet URL modules for route ownership
- feature selectors/services for context and workflows
- `cabinet/views/...` only when the project already centralizes those screens there
- `cabinet/templates/cabinet/<feature>/...` for cabinet templates in this project

The `cabinet` app owns the shell, auth, shared cabinet services, and project-level cabinet screens.

## Navigation rules

- Use `TopbarEntry` for staff top navigation modules.
- Use `SidebarItem` for the active module's left navigation.
- Use `settings_url` for the bottom Settings link.
- Do not add Settings as a normal sidebar item when `settings_url` is present.
- Keep sidebar items as real product pages, not placeholders.

Every cabinet view for a module must set:

```python
request.cabinet_module = "<module>"
```

Use a base class with `dispatch()` for CBVs. Use a render helper for function views.

## Existing module examples

- Booking: `features.booking.cabinet` registers `booking`; cabinet views set `request.cabinet_module = "booking"`.
- Conversations: `features.conversations.cabinet` registers inbox/campaign navigation.
- Staff: `features.booking.cabinet` currently registers staff navigation.
- Business/analytics/ops: project-level cabinet registrations live in `system.cabinet`.

Follow existing ownership unless a cleaner feature boundary is clearly needed.

## View rules

Views stay thin: parse request, call selectors for GET/read screens, call services/workflows for POST/actions, render/redirect/respond.

Do not put query-heavy tables, booking workflow rules, campaign actions, or notification side effects directly in views.

## Template rules

- Extend existing cabinet base templates.
- Use existing cabinet components and Bootstrap Icons.
- Keep UI dense, scannable, and work-focused.
- Do not apply public site styling to cabinet screens.
- Keep actions close to the object they affect.

## Cabinet settings

Module settings should usually be reached through the bottom `settings_url`.

Do not duplicate a module Settings item in the main sidebar unless there is a deliberate product reason.

## Tests

Add or update tests when cabinet URL routing, active module/sidebar behavior, topbar/sidebar/settings registration, POST actions, or selector context changes.
