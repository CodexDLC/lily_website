---
name: lily-feature-boundary-decision
description: Load this skill when deciding whether a Lily change belongs in an existing feature, a new feature, system, cabinet, booking, conversations, notifications, main, workers, or another module.
---

# Lily Feature Boundary Decision

Use this before creating new modules or placing new domain behavior.

## Default boundaries

- `core`: Django project configuration, root URLs, settings, runtime integration.
- `system`: site-wide settings, user/client models, global cabinet registrations, global management commands.
- `cabinet`: cabinet shell, auth, shared cabinet views/services/templates, staff/client operational screens.
- `features.booking`: booking domain, public booking flow, appointments, masters, schedules, booking cabinet.
- `features.conversations`: inbox/conversations/imported mail/campaigns and messaging workflows.
- `features.notifications`: notification logs and notification operations.
- `features.main`: public marketing/content pages such as home, services, team, FAQ, contacts.
- `workers`: background task execution and worker-facing orchestration.

## Extend an existing feature when

- the request uses that feature's domain language
- the feature already owns the model or route
- the new behavior shares existing selectors/services/workflows
- no separate navigation/API/admin surface is emerging

## Create a new feature when

- it has its own domain nouns and lifecycle
- it needs its own routes, selectors, services, models, templates, and tests
- putting it in `system` would make `system` a dumping ground
- it is operationally separate from booking/conversations/main

## Cabinet ownership

Cabinet navigation does not mean implementation belongs in the `cabinet` app.

If a cabinet page operates on a feature domain, keep implementation near that feature and register it with cabinet.

Examples:

- booking operations belong to `features.booking` plus cabinet templates/views
- conversations mailbox/campaigns belong to `features.conversations`
- ops/notifications belong to `features.notifications` or operational system code
- shared shell/auth helpers belong to `cabinet`

## System ownership

Use `system` for global site settings, user/client records shared across features, global cabinet dashboard registration, and site-wide management commands.

Do not use `system` for feature-specific workflows.

## Decision output

Before editing, state:

`Owning module: <module>. Reason: <one sentence>. Layout: <models/views/selectors/services/templates/etc.>`

If uncertain, choose the narrowest feature that owns the domain without coupling unrelated workflows.
