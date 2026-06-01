---
name: lily-change-triage
description: Load this skill for any Lily request to change, add, fix, or adjust public-site behavior, cabinet behavior, templates, models, CSS/JS assets, navigation, or admin surfaces. Use it first to classify the request before editing.
---

# Lily Change Triage

Use this before changing Lily code when the request is phrased in product terms.

## Classify the surface

- **Public site**: visitor-facing pages, booking flow, services, team, FAQ, contacts, legal pages.
- **Cabinet**: staff/client dashboard, booking operations, conversations, analytics, ops.
- **Admin**: Django admin/Unfold model editing.
- **Assets**: public CSS/JS, cabinet CSS/JS, static compilation.
- **Workers/integrations**: notification worker, system worker, Redis, Mailpit/email, Telegram/API integrations.

If a request touches multiple surfaces, name the primary surface and isolate cross-surface changes.

## Classify the change type

- **Template-only**: existing context already has all data.
- **Selector-context change**: templates need existing data in a better shape.
- **Model/schema change**: a new field/entity/relation/migration is needed.
- **Service/workflow change**: user action writes data, sends messages, changes status, or triggers side effects.
- **Asset change**: CSS/JS source or compiler config changes.
- **Navigation/registration change**: cabinet topbar/sidebar/settings_url, public URLs, menus.
- **Feature boundary decision**: ownership is unclear or a new domain is emerging.

Do not treat a template request as template-only if the required data belongs in models/selectors.

## Route to skills

- Public templates/pages: use `lily-public-template-change`.
- Cabinet changes: use `lily-cabinet-feature-change`.
- Models/fields/migrations/admin: use `lily-model-schema-change`.
- Reads/writes/context/workflows: use `lily-selector-service-discipline`.
- Feature ownership: use `lily-feature-boundary-decision`.
- CSS/JS/static bundles: use `lily-static-assets`.

## Before editing

State the classification in one concise update:

`Surface: <public/cabinet/admin/assets/...>. Change type: <template/selector/model/service/...>. Owning feature: <feature>.`

Then make the smallest change that preserves feature boundaries and compiled asset rules.
