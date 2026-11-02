---
name: lily-change-triage
description: Route ambiguous or cross-surface Lily product changes to the owning module and relevant project skills. Skip routine documentation work and changes whose owner and surface are already clear.
---

# Lily Change Triage

Use when a product request leaves the implementation boundary unclear. Do not load all Lily skills for every change.

Distinguish the public site, staff/client cabinet, Django admin, static bundles, and background workers. A cabinet page can operate on a feature-owned domain; its screen location does not determine model ownership.

Choose the affected path before editing: existing template context, additional read/context data, stored schema, write workflow, navigation registration, or compiled assets. A missing field in a template is not necessarily a template-only change.

Load only the guidance required by the task:

- Visitor pages and public booking rendering: [public templates](../lily-public-template-change/SKILL.md).
- Staff/client screens and module navigation: [cabinet](../lily-cabinet-feature-change/SKILL.md).
- Fields, migrations, translated content or admin data: [schema](../lily-model-schema-change/SKILL.md).
- Reads, writes, context or booking integration: [selectors/services](../lily-selector-service-discipline/SKILL.md).
- Unclear owner or a proposed new module: [feature boundaries](../lily-feature-boundary-decision/SKILL.md).
- CSS/JS source or build output: [static assets](../lily-static-assets/SKILL.md).

Explain the chosen owner when it resolves an ambiguity; no fixed status-message format is required. These are application skills, not substitutes for library usage documentation. Verification for code changes follows repository `AGENTS.md`.
