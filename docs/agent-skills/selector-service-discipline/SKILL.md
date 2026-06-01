---
name: lily-selector-service-discipline
description: Load this skill when implementing Lily read paths, write paths, template context assembly, cabinet/page context, form/admin actions, status changes, booking/conversation workflows, side effects, or cross-feature orchestration.
---

# Lily Selector And Service Discipline

Use this to keep business logic out of views and templates.

## Read path

Use selectors for reads:

`view -> selector -> context/data -> template`

Selectors own query composition, filters/search/status buckets, related-object loading, list/detail retrieval, counts, dashboard summaries, template-context assembly, and read DTO/state construction.

Selectors must not mutate database state.

## Write path

Use services for writes:

`view/admin/action -> service -> models/side effects`

Services own creates/updates/deletes, booking status transitions, conversation/message actions, ordering mutations, transactions, notification dispatch, cache/Redis invalidation, and worker orchestration.

Services should not render templates.

## View role

Views should only parse request params/form data, call selectors or services, apply auth/permission decorators or mixins, and return render/redirect/HTTP response.

If a view grows query-heavy or business-heavy branches, move that logic to selectors/services.

## Template role

Templates should display prepared data and simple conditionals only.

Do not make domain decisions in templates, query data from templates, or duplicate status/workflow logic in markup.

## Naming guidance

Selectors:

- `get_<thing>()`
- `get_<thing>_or_404()`
- `get_<thing>_context()`
- `get_<thing>_counts()`
- `list_<things>()`

Services:

- `create_<thing>()`
- `update_<thing>()`
- `mark_<thing>_<state>()`
- `send_<thing>()`
- `sync_<thing>()`
- `perform_<domain>_action()`

Keep names domain-specific.

## Tests

Test selectors for filters, counts, status buckets, and context shape.

Test services for state changes, transactions, side effects, invalid input, and permission/business rules.

Test views for URL integration, auth/permissions, POST redirects, HTMX responses, and cabinet module context.
