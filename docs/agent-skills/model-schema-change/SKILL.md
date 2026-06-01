---
name: lily-model-schema-change
description: Load this skill when adding or changing Lily Django models, fields, relationships, migrations, admin fields, translated fields, fixtures, or schema-backed template/cabinet data.
---

# Lily Model And Schema Change

Use this before adding fields or models.

## Ownership decision

Choose the owning app before editing:

- `features.booking`: appointments, appointment groups, masters, schedules, booking settings and booking workflow data.
- `features.conversations`: threads/messages/imported mail/campaigns/recipients and messaging workflow data.
- `features.main`: public marketing/content models if the domain is public site content.
- `features.notifications`: notification logs/ops-specific notification data.
- `system`: global site settings, users/clients, cross-site shared settings.
- new `features.<name>`: distinct product capability with its own routes/models/workflows.

Do not put feature-domain models in `system` just because multiple screens display them.

## Schema change workflow

1. Identify the owning feature and model package/file.
2. Add or change the model field/relation.
3. Add migration.
4. Update modeltranslation registration for public/editor-facing translated text.
5. Update admin fieldsets/list displays/search where editors need the field.
6. Update selectors so templates receive data intentionally.
7. Update services for writes/workflows.
8. Update templates/forms after the data path is clear.
9. Add tests for selector/service behavior and critical view integration.

## Translation rules

Lily uses `django-modeltranslation`.

For user-facing text fields:

- register fields in the feature's `translation.py`
- rely on modeltranslation-generated language fields
- do not manually add parallel `field_en/field_de/...` fields unless modeltranslation already owns them

For UI labels, follow existing use of Django translation helpers.

## Booking data

Booking domain changes should respect existing `codex_django.booking` mixins/contracts and Lily project providers.

Do not bypass the booking engine/provider layer for workflow behavior unless the change is strictly local to a model/admin display.

## Conversations/notifications data

Conversation and campaign data should stay in `features.conversations`; notification operational logs should stay in `features.notifications` or the established notification model location.

Side effects such as sending mail or scheduling jobs belong in services/workflows, not model field setters or templates.

## Migration care

- Keep migrations focused.
- Preserve existing booking/client/conversation data.
- Use data migrations only when existing rows need normalization.
- Avoid casual renames/drops.
- Choose conservative defaults.
