---
name: lily-public-template-change
description: Load this skill when changing Lily public-site Django templates, visitor-facing pages, booking flow templates, service/team/FAQ/contact pages, public CSS, or public route rendering.
---

# Lily Public Template Change

Use this for visitor-facing Lily pages and templates.

## Public surface

Public site work usually lives in:

- `templates/` for site templates and includes
- `features.main` for marketing/content pages
- `features.booking.views.public` for public booking flow
- `static/css/` for public CSS sources and compiled `app.css`

Use `lily-static-assets` for CSS/JS changes.

## Template change workflow

1. Locate the template and the view/selector/service that feeds it.
2. Check whether the required data already exists in context.
3. If data exists, change only template/CSS.
4. If data exists in models but not context, update the selector/context builder.
5. If data does not exist, use `lily-model-schema-change` and decide the owning feature.
6. Add tests when routing, context shape, booking flow behavior, or important rendering logic changes.

## Do not

- Do not put feature queries directly in templates.
- Do not place public booking workflow logic in templates.
- Do not mix cabinet CSS/classes into public site templates.
- Do not edit compiled CSS output directly.
- Do not create static hard-coded pages when the content belongs to an existing model/service flow.

## Public booking flow

Public booking changes are more sensitive than normal marketing pages.

Keep the flow aligned with:

- `features.booking.views.public`
- booking selectors/providers
- booking services/persistence
- existing booking templates

Do not bypass booking provider/engine contracts for availability, slot selection, or appointment creation.

## Visual rules

- Preserve Lily's existing brand and layout conventions.
- Reuse existing public components in `static/css/components/` and site/page CSS.
- Keep mobile behavior explicit; check adaptive CSS directories before adding one-off media queries.
- Keep text and controls from overlapping at mobile and desktop widths.
