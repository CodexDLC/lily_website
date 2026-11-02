---
name: lily-model-schema-change
description: Maintain Lily model, migration, translated-field and admin contracts when stored data changes. Skip template-only or query-only work.
---

# Lily Model and Schema Changes

For uncertain ownership use [feature boundaries](../lily-feature-boundary-decision/SKILL.md); do not repeat or reinvent that map. Inspect the existing model package, migrations and admin registration before adding fields.

Lily uses modeltranslation for selected editorial fields, not every string. Current registrations are in `src/lily_backend/features/main/translation.py` (services/categories/combos), `features/booking/translation.py` (master content), and `src/lily_backend/system/translation.py` (site/static/email/SEO content). `features/conversations/translations.py` is currently only a placeholder; do not assume it registers models.

For a translated content field, update the owner's registration and generate the corresponding migration. Do not manually define competing language-suffixed model fields. For UI labels follow the existing Django translation usage. Update admin/forms and the affected context path when editors or screens need the new field.

Booking models participate in the runtime provider's model mapping and persistence contract. For booking schema changes read [booking integration](../lily-selector-service-discipline/references/booking-integration.md) before choosing fields or defaults.

Preserve existing client/booking/conversation data. A rename, removal or default change must account for existing rows; do not treat it as an empty-database setup. Keep dispatch and job scheduling in the established workflow instead of adding side effects to field setters.

Verify the affected model/translation/admin behavior and migration compatibility using the project's verification workflow. Do not run migrations against a live database as part of authoring a skill or reviewing schema instructions.
